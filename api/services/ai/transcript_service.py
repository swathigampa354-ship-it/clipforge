"""
Transcript service — handles transcript storage and processing
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID as UUIDType

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from api.core.database import AsyncSessionLocal
from api.models.core import Transcript, Video
from api.services.ai.analysis_engine import Segment

logger = logging.getLogger(__name__)


class TranscriptService:
    """Manages transcript lifecycle"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_transcript(
        self,
        video_id: UUIDType,
        provider: str,
        language: str,
        content: dict,
        full_text: str,
    ) -> Transcript:
        """Store transcript in database"""
        transcript = Transcript(
            id=__import__("uuid").uuid4(),
            video_id=video_id,
            provider=provider,
            language=language,
            content=content,
            full_text=full_text,
            status="completed",
        )
        self.db.add(transcript)
        await self.db.commit()
        await self.db.refresh(transcript)
        logger.info(f"Stored transcript {transcript.id} for video {video_id}")
        return transcript

    async def get_transcript(self, video_id: UUIDType) -> Optional[Transcript]:
        """Get completed transcript for a video"""
        result = await self.db.execute(
            select(Transcript).where(Transcript.video_id == video_id, Transcript.status == "completed")
        )
        return result.scalar_one_or_none()

    async def update_status(self, video_id: UUIDType, status: str) -> None:
        """Update transcript status"""
        result = await self.db.execute(
            select(Transcript).where(Transcript.video_id == video_id)
        )
        transcript = result.scalar_one_or_none()
        if transcript:
            transcript.status = status
            await self.db.commit()

    async def get_word_timestamps(self, video_id: UUIDType) -> List[dict]:
        """Get word-level timestamps for a video"""
        transcript = await self.get_transcript(video_id)
        if transcript and transcript.content:
            return transcript.content.get("words", [])
        return []

    async def get_segments(self, video_id: UUIDType) -> List[dict]:
        """Get segment-level data for a video"""
        transcript = await self.get_transcript(video_id)
        if transcript and transcript.content:
            return transcript.content.get("segments", [])
        return []

    async def get_full_text(self, video_id: UUIDType) -> str:
        """Get full transcript text for a video"""
        transcript = await self.get_transcript(video_id)
        return transcript.full_text if transcript else ""

    async def get_segments_as_objects(self, video_id: UUIDType) -> List[Segment]:
        """Get segments as Segment objects"""
        word_timestamps = await self.get_word_timestamps(video_id)
        segments_data = await self.get_segments(video_id)

        segments = []
        for seg_data in segments_data:
            seg_words = [
                {"word": w["word"], "start": w["start"], "end": w["end"]}
                for w in word_timestamps
                if seg_data["start"] <= w["start"] <= seg_data["end"]
            ]
            segments.append(Segment(
                start_time=seg_data["start"],
                end_time=seg_data["end"],
                text=seg_data.get("text", ""),
                words=seg_words,
            ))

        return segments

    async def get_transcript_stats(self, video_id: UUIDType) -> dict:
        """Get statistics about a transcript"""
        transcript = await self.get_transcript(video_id)
        if not transcript or not transcript.content:
            return {"status": "not_found"}

        words = transcript.content.get("words", [])
        segments = transcript.content.get("segments", [])

        return {
            "provider": transcript.provider,
            "language": transcript.language,
            "total_words": len(words),
            "total_segments": len(segments),
            "duration": transcript.content.get("duration", 0),
            "status": transcript.status,
            "created_at": str(transcript.created_at),
        }