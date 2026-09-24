"""
Clip detection service — orchestrates the full clip detection pipeline
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional, List
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from uuid import UUID as UUIDType

from api.core.database import AsyncSessionLocal
from api.models.core import ClipCandidate, Video, Transcript
from api.services.ai.analysis_engine import (
    AIAnalysisService,
    TranscriptProcessor,
    Segment,
    AnalysisResult,
)
from api.app.config import settings

logger = logging.getLogger(__name__)


class ClipDetectionService:
    """Service for detecting and scoring clip candidates"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.analysis = AIAnalysisService()

    async def detect_clips(self, video_id: UUIDType, project_id: UUIDType) -> dict:
        """
        Main entry point for clip detection
        
        1. Get transcript
        2. Process into segments
        3. Detect candidates
        4. Score and deduplicate
        5. Store candidates in DB
        6. Return results
        """
        # Get video
        video_result = await self.db.execute(select(Video).where(Video.id == video_id))
        video = video_result.scalar_one_or_none()
        if not video:
            raise ValueError(f"Video {video_id} not found")

        # Get transcript
        transcript = await self._get_transcript(video_id)
        if not transcript:
            raise ValueError(f"No transcript found for video {video_id}")

        # Parse segments
        segments = self._parse_segments(transcript)

        # Run AI analysis
        result = await self.analysis.analyze(video_id, transcript, segments)

        # Store candidates in database
        await self._store_candidates(result, video_id)

        return {
            "video_id": str(video_id),
            "total_candidates": len(result.candidates),
            "candidates": [c.to_dict() for c in result.candidates],
            "topics": result.topics,
            "processing_time": result.processing_time_seconds,
            "segments_count": len(segments),
        }

    async def _get_transcript(self, video_id: UUIDType) -> Optional[dict]:
        """Get transcript for a video"""
        result = await self.db.execute(
            select(Transcript).where(Transcript.video_id == video_id, Transcript.status == "completed")
        )
        transcript = result.scalar_one_or_none()
        if transcript:
            return {
                "provider": transcript.provider,
                "language": transcript.language,
                "content": transcript.content,
                "full_text": transcript.full_text,
                "duration": None,
                "segments": transcript.content.get("segments", []) if transcript.content else [],
                "words": transcript.content.get("words", []) if transcript.content else [],
            }
        return None

    def _parse_segments(self, transcript: dict) -> List[Segment]:
        """Parse transcript into Segment objects"""
        segments = []
        seg_data = transcript.get("segments", [])
        words = transcript.get("words", [])

        for seg in seg_data:
            seg_words = [w for w in words if seg["start"] <= w.get("start", 0) <= seg["end"]]
            segments.append(Segment(
                start_time=seg["start"],
                end_time=seg["end"],
                text=seg.get("text", ""),
                words=seg_words,
            ))

        return segments

    async def _store_candidates(self, result: AnalysisResult, video_id: UUIDType) -> None:
        """Store clip candidates in database"""
        for candidate in result.candidates:
            db_candidate = ClipCandidate(
                id=candidate.id,
                video_id=video_id,
                start_time=candidate.start_time,
                end_time=candidate.end_time,
                score=candidate.score,
                hook_text=candidate.hook_text,
                category=candidate.category,
                confidence=candidate.confidence,
                strategy=candidate.strategy.value,
                metadata=candidate.metadata,
                is_duplicate=candidate.is_duplicate,
                selected=candidate.selected,
            )
            self.db.add(db_candidate)

        await self.db.commit()
        logger.info(f"Stored {len(result.candidates)} candidates in database")

    async def get_candidates(self, video_id: UUIDType) -> List[ClipCandidate]:
        """Get all candidates for a video"""
        result = await self.db.execute(
            select(ClipCandidate).where(ClipCandidate.video_id == video_id).order_by(ClipCandidate.score.desc())
        )
        return list(result.scalars().all())

    async def get_top_candidates(self, video_id: UUIDType, limit: int = 10) -> List[ClipCandidate]:
        """Get top N candidates for a video"""
        result = await self.db.execute(
            select(ClipCandidate)
            .where(ClipCandidate.video_id == video_id, ~ClipCandidate.is_duplicate)
            .order_by(ClipCandidate.score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def select_candidate(self, candidate_id: UUIDType) -> bool:
        """Mark a candidate as selected"""
        result = await self.db.execute(select(ClipCandidate).where(ClipCandidate.id == candidate_id))
        candidate = result.scalar_one_or_none()
        if candidate:
            candidate.selected = True
            await self.db.commit()
            return True
        return False


class ScoringConfig:
    """Configuration for the scoring system"""

    DEFAULT_WEIGHTS = {
        "hook_score": 1.2,
        "information_density": 1.0,
        "emotional_intensity": 0.9,
        "novelty": 0.8,
        "narrative_completeness": 0.7,
        "curiosity": 0.8,
        "quotability": 1.0,
        "audience_relevance": 0.9,
        "dead_air_penalty": -0.5,
        "context_dependency_penalty": -0.3,
        "duplicate_penalty": -0.6,
    }

    DEFAULT_THRESHOLDS = {
        "minimum_score": 60.0,
        "good_score": 75.0,
        "excellent_score": 90.0,
        "max_candidates": 20,
        "min_duration": 10,
        "max_duration": 60,
        "min_gap_between_clips": 5,
    }

    @classmethod
    def from_env(cls) -> dict:
        """Load configuration from environment variables"""
        return {
            "weights": {
                "hook_score": float(os.environ.get("SCORE_HOOK", "1.2")),
                "information_density": float(os.environ.get("SCORE_DENSITY", "1.0")),
                "emotional_intensity": float(os.environ.get("SCORE_EMOTION", "0.9")),
                "novelty": float(os.environ.get("SCORE_NOVELTY", "0.8")),
                "narrative_completeness": float(os.environ.get("SCORE_NARRATIVE", "0.7")),
                "curiosity": float(os.environ.get("SCORE_CURIOSITY", "0.8")),
                "quotability": float(os.environ.get("SCORE_QUOTABLE", "1.0")),
                "audience_relevance": float(os.environ.get("SCORE_RELEVANCE", "0.9")),
            },
            "thresholds": {
                "minimum_score": float(os.environ.get("CLIPPYME_MIN_VIRAL_SCORE", "60")),
                "max_candidates": int(os.environ.get("CLIPPYME_MAX_CLIPS", "20")),
                "min_duration": int(os.environ.get("CLIPPYME_MIN_DURATION", "10")),
                "max_duration": int(os.environ.get("CLIPPYME_MAX_DURATION", "60")),
            },
        }


import os