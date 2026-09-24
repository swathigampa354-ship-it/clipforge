"""
AI Analysis Router — wraps AI services in API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional

from api.core.database import get_db
from api.core.auth import get_current_user
from api.schemas.common import ApiResponse
from api.models.user import User
from api.services.ai.analysis_engine import AIAnalysisService, TranscriptProcessor
from api.services.ai.clip_detection import ClipDetectionService
from api.services.ai.transcript_service import TranscriptService

router = APIRouter()


@router.post("/analyze")
async def analyze_video(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run complete AI analysis on a video"""
    try:
        # Get transcript
        transcript_service = TranscriptService(db)
        transcript = await transcript_service.get_transcript(video_id)
        if not transcript:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found")

        # Get segments
        segments = await transcript_service.get_segments_as_objects(video_id)

        # Run AI analysis
        analysis = AIAnalysisService()
        result = await analysis.analyze(
            video_id=str(video_id),
            transcript=transcript.content,
            segments=segments,
        )

        return ApiResponse(data={
            "candidates": [c.to_dict() for c in result.candidates],
            "topics": result.topics,
            "processing_time": result.processing_time_seconds,
            "total_candidates": len(result.candidates),
        }, message="Analysis complete")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/candidates/{video_id}")
async def get_candidates(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 10,
):
    """Get clip candidates for a video"""
    try:
        detection = ClipDetectionService(db)
        candidates = await detection.get_top_candidates(video_id, limit=limit)
        return ApiResponse(data=[c.to_dict() for c in candidates])
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/select/{candidate_id}")
async def select_candidate(
    candidate_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Select a clip candidate"""
    try:
        detection = ClipDetectionService(db)
        selected = await detection.select_candidate(candidate_id)
        if not selected:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
        return ApiResponse(message="Candidate selected")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/segment")
async def segment_transcript(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Segment a transcript into analyzable parts"""
    try:
        transcript_service = TranscriptService(db)
        segments = await transcript_service.get_segments_as_objects(video_id)
        transcript = await transcript_service.get_transcript(video_id)

        if not transcript:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found")

        result = TranscriptProcessor.segment_by_sentences(transcript.content)

        return ApiResponse(data={
            "total_segments": len(result),
            "segments": [
                {"start": s.start_time, "end": s.end_time, "text": s.text[:100]}
                for s in result
            ],
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/transcribe/{video_id}")
async def transcribe_video(
    video_id: UUID,
    provider: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger transcription for a video"""
    try:
        from api.services.video_service import VideoService
        video_service = VideoService(db)
        result = await video_service.transcribe_video(video_id, current_user.id)
        return ApiResponse(data=result, message="Transcription started")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/status/{video_id}")
async def get_analysis_status(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get AI analysis status for a video"""
    try:
        transcript_service = TranscriptService(db)
        stats = await transcript_service.get_transcript_stats(video_id)
        return ApiResponse(data=stats)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))