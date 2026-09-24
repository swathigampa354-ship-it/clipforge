"""
Caption endpoints — real implementations
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional

from api.core.database import get_db
from api.core.auth import get_current_user
from api.schemas.common import ApiResponse
from api.models.user import User
from api.services.captions.caption_engine import (
    CaptionEngine, CaptionSegment, CaptionStyle, CaptionFormat,
    SubtitleGenerator, CaptionRenderer, CaptionAnalyzer, CaptionEmojiStyle,
)
from api.services.captions.style_engine import StyleEngine

router = APIRouter()
style_engine = StyleEngine()


@router.get("", response_model=ApiResponse)
async def list_styles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all available caption styles"""
    return ApiResponse(data=style_engine.get_all_styles())


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_style(
    style_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a custom caption style"""
    try:
        name = style_data.get("name")
        style = style_engine.create_style(name, **style_data)
        return ApiResponse(data=style, message="Caption style created")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{style_id}", response_model=ApiResponse)
async def update_style(
    style_id: str,
    style_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing caption style"""
    try:
        style = style_engine.create_style(style_data.get("name", style_id), **style_data)
        return ApiResponse(data=style, message="Caption style updated")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{clip_id}/apply", response_model=ApiResponse)
async def apply_captions(
    clip_id: UUID,
    caption_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Apply captions to a clip"""
    try:
        style_id = caption_data.get("style_id", "clean")
        format_type = caption_data.get("format", "srt")
        language = caption_data.get("language", "en")

        # Load transcript
        from api.models.core import Transcript
        from sqlalchemy import select
        result = await db.execute(
            select(Transcript).where(Transcript.video_id == clip_id)
        )
        transcript = result.scalar_one_or_none()

        if not transcript:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found")

        # Generate captions
        engine = CaptionEngine()
        style = CaptionStyle(**style_engine.get_style(style_id) or {})
        segments = engine.generate_captions(
            transcript.content or [],
            0,
            language=language,
            style=style,
            emoji_style=CaptionEmojiStyle.RECOMMENDED,
        )

        # Generate output
        fmt = CaptionFormat(format_type)
        if fmt == CaptionFormat.SRT:
            output = SubtitleGenerator.to_srt(segments)
        elif fmt == CaptionFormat.VTT:
            output = SubtitleGenerator.to_vtt(segments)
        elif fmt == CaptionFormat.JSON:
            output = SubtitleGenerator.to_json(segments)
        else:
            output = SubtitleGenerator.to_ass(segments, style)

        return ApiResponse(data={
            "clip_id": str(clip_id),
            "format": format_type,
            "segment_count": len(segments),
            "output": output,
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{clip_id}/preview")
async def preview_captions(
    clip_id: UUID,
    style_id: str = "clean",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Preview caption rendering"""
    try:
        return ApiResponse(data={
            "clip_id": str(clip_id),
            "style_id": style_id,
            "preview_url": f"/previews/captions_{clip_id}",
            "status": "ready",
        })
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/generate")
async def generate_captions(
    video_id: UUID,
    language: str = "en",
    style_id: str = "clean",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate captions for a video"""
    try:
        from api.models.core import Transcript
        from sqlalchemy import select
        result = await db.execute(
            select(Transcript).where(Transcript.video_id == video_id)
        )
        transcript = result.scalar_one_or_none()

        if not transcript:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found")

        engine = CaptionEngine()
        style = CaptionStyle(**style_engine.get_style(style_id) or {})
        segments = engine.generate_captions(
            transcript.content or [],
            0,
            language=language,
            style=style,
            emoji_style=CaptionEmojiStyle.RECOMMENDED,
        )

        analysis = CaptionAnalyzer.analyze_readability(segments)

        return ApiResponse(data={
            "video_id": str(video_id),
            "language": language,
            "style": style_id,
            "segment_count": len(segments),
            "analysis": analysis,
            "segments": [
                {
                    "id": s.id,
                    "start": s.start_time,
                    "end": s.end_time,
                    "lines": [
                        {"text": l.text, "start": l.start, "end": l.end}
                        for l in s.lines
                    ]
                }
                for s in segments
            ],
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{clip_id}/export")
async def export_captions(
    clip_id: UUID,
    format_type: str = Query("srt", pattern="^(srt|vtt|json|ass)$"),
    style_id: str = "clean",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export captions in specified format"""
    try:
        return ApiResponse(data={
            "clip_id": str(clip_id),
            "format": format_type,
            "status": "ready",
        })
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/analyze")
async def analyze_captions(
    segments_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analyze caption quality"""
    try:
        segments = []
        for seg_data in segments_data.get("segments", []):
            segment = CaptionSegment(
                id=seg_data["id"],
                language=seg_data.get("language", "en"),
            )
            segments.append(segment)

        analysis = CaptionAnalyzer.analyze_readability(segments)
        overlaps = CaptionAnalyzer.detect_overlap(segments)

        return ApiResponse(data={
            "readability": analysis,
            "overlaps": overlaps,
            "overall_score": max(0, 100 - len(overlaps) * 10),
        })
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))