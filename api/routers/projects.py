from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, update
from uuid import UUID
from typing import Optional, List
from datetime import datetime

from api.core.database import get_db
from api.models.core import Project, Video
from api.models.user import User
from api.schemas.projects import ProjectCreate, ProjectUpdate, ProjectResponse, VideoResponse
from api.schemas.common import ApiResponse
from api.core.auth import get_current_user
from api.services.project_service import ProjectService
from api.services.video_service import VideoService
from api.core.rate_limiter import rate_limiter

router = APIRouter()


@router.post("/projects", response_model=ApiResponse[ProjectResponse], status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    project = await service.create_project(current_user.id, payload)
    return ApiResponse(data=ProjectResponse.model_validate(project), message="Project created")


@router.get("/projects", response_model=ApiResponse[List[ProjectResponse]])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status_filter: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    service = ProjectService(db)
    projects = await service.list_projects(current_user.id, status_filter, limit, offset)
    return ApiResponse(data=[ProjectResponse.model_validate(p) for p in projects])


@router.get("/projects/{project_id}", response_model=ApiResponse[ProjectResponse])
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    project = await service.get_project(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ApiResponse(data=ProjectResponse.model_validate(project))


@router.put("/projects/{project_id}", response_model=ApiResponse[ProjectResponse])
async def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    project = await service.update_project(project_id, current_user.id, payload)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ApiResponse(data=ProjectResponse.model_validate(project))


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    await service.delete_project(project_id, current_user.id)
    return ApiResponse(message="Project deleted")


@router.get("/projects/{project_id}/videos", response_model=ApiResponse[List[VideoResponse]])
async def list_videos(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = VideoService(db)
    videos = await service.list_videos(project_id, current_user.id)
    return ApiResponse(data=[VideoResponse.model_validate(v) for v in videos])


from fastapi import APIRouter as APIRouterType
router = APIRouter()
