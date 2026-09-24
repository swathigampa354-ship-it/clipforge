from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional

from api.core.database import get_db
from api.core.auth import get_current_user
from api.schemas.common import ApiResponse
from api.models.user import User
from api.services.clip_service import ClipService

router = APIRouter()


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_clip(
    clip_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ClipService(db)
    clip = await service.create_clip(current_user.id, clip_data)
    return ApiResponse(data=clip, message="Clip created")


@router.get("", response_model=ApiResponse)
async def list_clips(
    video_id: Optional[UUID] = None,
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
):
    service = ClipService(db)
    clips = await service.list_clips(current_user.id, video_id, project_id, status, limit, offset)
    return ApiResponse(data=clips)


@router.get("/{clip_id}", response_model=ApiResponse)
async def get_clip(
    clip_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ClipService(db)
    clip = await service.get_clip(clip_id, current_user.id)
    if not clip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found")
    return ApiResponse(data=clip)


@router.put("/{clip_id}", response_model=ApiResponse)
async def update_clip(
    clip_id: UUID,
    clip_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ClipService(db)
    clip = await service.update_clip(clip_id, current_user.id, clip_data)
    if not clip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found")
    return ApiResponse(data=clip)


@router.post("/{clip_id}/render", response_model=ApiResponse)
async def render_clip(
    clip_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    render_type: str = "final",
):
    service = ClipService(db)
    job = await service.trigger_render(clip_id, current_user.id, render_type)
    return ApiResponse(data=job, message="Render queued")


@router.get("/{clip_id}/preview", response_model=ApiResponse)
async def get_preview(
    clip_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ClipService(db)
    preview = await service.get_preview(clip_id, current_user.id)
    return ApiResponse(data=preview)


@router.get("/{clip_id}/output", response_model=ApiResponse)
async def get_output(
    clip_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ClipService(db)
    output = await service.get_output(clip_id, current_user.id)
    return ApiResponse(data=output)


@router.delete("/{clip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clip(
    clip_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ClipService(db)
    await service.delete_clip(clip_id, current_user.id)
    return ApiResponse(message="Clip deleted")


@router.post("/{clip_id}/edit")
async def edit_clip(
    clip_id: UUID,
    edit_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ClipService(db)
    result = await service.edit_clip(clip_id, current_user.id, edit_data)
    return ApiResponse(data=result)


@router.post("/{clip_id}/select")
async def select_clip(
    clip_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ClipService(db)
    await service.select_clip(clip_id, current_user.id)
    return ApiResponse(message="Clip selected")


@router.post("/{clip_id}/deselect")
async def deselect_clip(
    clip_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ClipService(db)
    await service.deselect_clip(clip_id, current_user.id)
    return ApiResponse(message="Clip deselected")