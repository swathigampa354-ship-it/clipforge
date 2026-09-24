"""
Clip service for managing clips and their lifecycle
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func
from uuid import UUID as UUIDType

from api.core.database import AsyncSessionLocal, Base
from api.models.core import Clip, ClipCandidate, RenderJob, RenderOutput, Transcript
from api.models.user import User


class ClipService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_clip(self, user_id: UUIDType, data: dict) -> Clip:
        candidate_id = data.get("candidate_id")
        clip = Clip(
            id=uuid.uuid4(),
            video_id=data["video_id"],
            candidate_id=candidate_id,
            title=data.get("title"),
            description=data.get("description"),
            hashtags=data.get("hashtags", {}),
            start_time=data["start_time"],
            end_time=data["end_time"],
            aspect_ratio=data.get("aspect_ratio", "9:16"),
            reframe_path=data.get("reframe_path"),
            caption_style_id=data.get("caption_style_id"),
            status="draft",
        )
        self.db.add(clip)
        await self.db.commit()
        await self.db.refresh(clip)
        return clip

    async def list_clips(
        self, user_id: UUIDType,
        video_id: Optional[UUIDType] = None,
        project_id: Optional[UUIDType] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Clip]:
        query = select(Clip).join(User).where(Clip.id.in_(
            select(Clip.id)
        ))
        # Simplified query
        result = await self.db.execute(
            select(Clip).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def get_clip(self, clip_id: UUIDType, user_id: UUIDType) -> Optional[Clip]:
        result = await self.db.execute(select(Clip).where(Clip.id == clip_id))
        return result.scalar_one_or_none()

    async def update_clip(self, clip_id: UUIDType, user_id: UUIDType, data: dict) -> Optional[Clip]:
        clip = await self.get_clip(clip_id, user_id)
        if not clip:
            return None
        for field, value in data.items():
            setattr(clip, field, value)
        await self.db.commit()
        await self.db.refresh(clip)
        return clip

    async def delete_clip(self, clip_id: UUIDType, user_id: UUIDType) -> None:
        clip = await self.get_clip(clip_id, user_id)
        if clip:
            await self.db.delete(clip)
            await self.db.commit()

    async def trigger_render(self, clip_id: UUIDType, user_id: UUIDType, render_type: str = "final") -> dict:
        render_job = RenderJob(
            id=uuid.uuid4(),
            clip_id=clip_id,
            render_type=render_type,
            status="queued",
            progress=0.0,
        )
        self.db.add(render_job)
        await self.db.commit()
        await self.db.refresh(render_job)
        return {"job_id": str(render_job.id), "status": "queued"}

    async def get_preview(self, clip_id: UUIDType, user_id: UUIDType) -> dict:
        clip = await self.get_clip(clip_id, user_id)
        return {"clip_id": str(clip_id), "preview_url": f"/clips/{clip_id}/preview.mp4"}

    async def get_output(self, clip_id: UUIDType, user_id: UUIDType) -> dict:
        clip = await self.get_clip(clip_id, user_id)
        return {"clip_id": str(clip_id), "output_url": clip.output_url}

    async def select_clip(self, clip_id: UUIDType, user_id: UUIDType) -> None:
        clip = await self.get_clip(clip_id, user_id)
        if clip:
            clip.status = "rendering"
            await self.db.commit()

    async def deselect_clip(self, clip_id: UUIDType, user_id: UUIDType) -> None:
        clip = await self.get_clip(clip_id, user_id)
        if clip:
            clip.status = "draft"
            await self.db.commit()