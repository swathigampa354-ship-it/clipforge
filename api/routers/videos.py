from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional, List

from api.core.database import get_db
from api.core.auth import get_current_user
from api.schemas.common import ApiResponse
from api.core.rate_limiter import rate_limiter
from api.services.video_service import VideoService
from api.models.user import User

router = APIRouter()


@router.post("/videos/upload", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
@rate_limiter.limit("5/minute")
async def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    project_id: Optional[UUID] = Query(None),
):
    service = VideoService(db)
    result = await service.upload_video(current_user.id, file, project_id)
    return ApiResponse(data=result, message="Video uploaded successfully")


@router.post("/videos/import", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
@rate_limiter.limit("3/minute")
async def import_video(
    url: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    project_id: Optional[UUID] = None,
):
    service = VideoService(db)
    result = await service.import_video(current_user.id, url, project_id)
    return ApiResponse(data=result, message="Video import initiated")


@router.get("/videos/{video_id}", response_model=ApiResponse)
async def get_video(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = VideoService(db)
    video = await service.get_video(video_id, current_user.id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return ApiResponse(data=video)


@router.post("/videos/{video_id}/analyze", response_model=ApiResponse)
async def analyze_video(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = VideoService(db)
    job = await service.start_analysis(video_id, current_user.id)
    return ApiResponse(data=job, message="Analysis started")


@router.get("/videos/{video_id}/status", response_model=ApiResponse)
async def get_video_status(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = VideoService(db)
    status_result = await service.get_video_status(video_id, current_user.id)
    return ApiResponse(data=status_result)


@router.get("/videos/{video_id}/clips", response_model=ApiResponse)
async def get_video_clips(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = VideoService(db)
    clips = await service.get_video_clips(video_id, current_user.id)
    return ApiResponse(data=clips)


@router.delete("/videos/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = VideoService(db)
    await service.delete_video(video_id, current_user.id)
    return ApiResponse(message="Video deleted")


@router.post("/videos/{video_id}/thumbnail")
async def generate_thumbnail(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = VideoService(db)
    result = await service.generate_thumbnail(video_id, current_user.id)
    return ApiResponse(data=result)


@router.get("/videos/{video_id}/transcript")
async def get_transcript(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = VideoService(db)
    transcript = await service.get_transcript(video_id, current_user.id)
    return ApiResponse(data=transcript)