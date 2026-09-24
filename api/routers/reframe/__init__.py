"""
Reframe router — API endpoints for smart reframing
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional, List

from api.core.database import get_db
from api.core.auth import get_current_user
from api.schemas.common import ApiResponse
from api.models.user import User
from api.services.reframe.face_detector import ReframeService, FaceDetectionService

router = APIRouter()


@router.post("/{video_id}/generate")
async def generate_reframe_path(
    video_id: UUID,
    mode: str = "auto",
    aspect_ratio: str = Query("9:16", pattern="^(9:16|1:1|16:9)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate reframe path for a video"""
    try:
        service = ReframeService(db)
        result = await service.reframe_video(video_id, aspect_ratio=aspect_ratio, mode=mode)
        return ApiResponse(data=result, message="Reframe path generated")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{video_id}/path")
async def get_reframe_path(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the generated camera path for a video"""
    try:
        service = FaceDetectionService(db)
        path = await service.get_camera_path(video_id)
        if not path:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reframe path not found")
        return ApiResponse(data={
            "video_id": str(video_id),
            "keyframes": [
                {
                    "time": kf.time,
                    "crop_x": kf.crop_x,
                    "crop_y": kf.crop_y,
                    "crop_w": kf.crop_w,
                    "crop_h": kf.crop_h,
                    "zoom": kf.zoom,
                    "strategy": kf.strategy.value,
                    "locked": kf.locked,
                }
                for kf in path.keyframes
            ],
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{clip_id}/reframe")
async def reframe_clip(
    clip_id: UUID,
    clip_start: float = 0.0,
    clip_end: float = 30.0,
    source_path: str = "",
    aspect_ratio: str = "9:16",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reframe a specific clip"""
    try:
        service = ReframeService(db)
        result = await service.reframe_clip(
            clip_id, clip_start, clip_end, source_path,
            output_path=f"/reframed/{clip_id}.mp4",
            aspect_ratio=aspect_ratio,
        )
        return ApiResponse(data=result, message="Clip reframed")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/detect/{video_id}")
async def detect_faces(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Detect faces and speakers in a video"""
    try:
        service = FaceDetectionService(db)
        result = await service.detect_faces(video_id)
        return ApiResponse(data=result, message="Face detection complete")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/speakers/{video_id}")
async def get_speakers(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get speaker tracking data for a video"""
    try:
        service = FaceDetectionService(db)
        result = await service.track_speakers(video_id, [])
        return ApiResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/preview/{video_id}")
async def preview_reframe(
    video_id: UUID,
    time: float = 5.0,
    aspect_ratio: str = "9:16",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Preview reframe at a specific time"""
    try:
        service = ReframeService(db)
        result = await service.reframe_video(video_id, aspect_ratio=aspect_ratio)
        return ApiResponse(data=result, message="Preview ready")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))