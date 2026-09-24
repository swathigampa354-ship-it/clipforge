# Project service
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from uuid import UUID
from datetime import datetime
from typing import Optional, List

from api.core.database import AsyncSessionLocal
from api.models.core import Project, Video
from api.schemas.projects import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_project(self, user_id: UUID, payload: ProjectCreate) -> Project:
        project = Project(
            user_id=user_id,
            name=payload.name,
            description=payload.description,
            source_type=payload.source_type,
        )
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def list_projects(self, user_id: UUID, status_filter: Optional[str] = None, limit: int = 20, offset: int = 0) -> List[Project]:
        query = select(Project).where(Project.user_id == user_id)
        if status_filter:
            query = query.where(Project.status == status_filter)
        query = query.order_by(Project.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_project(self, project_id: UUID, user_id: UUID) -> Optional[Project]:
        query = select(Project).where(Project.id == project_id, Project.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_project(self, project_id: UUID, user_id: UUID, payload: ProjectUpdate) -> Optional[Project]:
        project = await self.get_project(project_id, user_id)
        if not project:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete_project(self, project_id: UUID, user_id: UUID) -> None:
        project = await self.get_project(project_id, user_id)
        if project:
            await self.db.delete(project)
            await self.db.commit()


class VideoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload_video(self, user_id: UUID, file, project_id: Optional[UUID]) -> dict:
        import uuid
        from api.models.core import Video

        video = Video(
            id=uuid.uuid4(),
            project_id=project_id,
            original_filename=file.filename or "unknown",
            status="uploading",
            file_size_bytes=len(await file.read()),
        )
        self.db.add(video)
        await self.db.commit()
        await self.db.refresh(video)
        return {"id": str(video.id), "status": video.status, "filename": video.original_filename}

    async def import_video(self, user_id: UUID, url: str, project_id: Optional[UUID]) -> dict:
        import uuid
        from api.models.core import Video

        video = Video(
            id=uuid.uuid4(),
            project_id=project_id,
            original_filename=url.split('/')[-1] or "imported",
            source_url=url,
            status="uploading",
        )
        self.db.add(video)
        await self.db.commit()
        await self.db.refresh(video)
        return {"id": str(video.id), "status": video.status, "url": url}

    async def get_video(self, video_id: UUID, user_id: UUID) -> Optional[Video]:
        from api.models.core import Video
        query = select(Video).join(Project).where(Video.id == video_id, Project.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def start_analysis(self, video_id: UUID, user_id: UUID) -> dict:
        return {"job_id": str(uuid.uuid4()), "video_id": str(video_id), "status": "queued"}

    async def get_video_status(self, video_id: UUID, user_id: UUID) -> dict:
        return {"video_id": str(video_id), "status": "uploading"}

    async def get_video_clips(self, video_id: UUID, user_id: UUID) -> list:
        return []

    async def delete_video(self, video_id: UUID, user_id: UUID) -> None:
        pass
