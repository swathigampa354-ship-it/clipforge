# Project schemas
from pydantic import BaseModel, Field, UUID
from typing import Optional
from enum import Enum
from datetime import datetime


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    source_type: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    status: str
    source_type: Optional[str] = None
    source_url: Optional[str] = None
    source_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VideoResponse(BaseModel):
    id: UUID
    project_id: UUID
    original_filename: str
    storage_path: Optional[str] = None
    duration_seconds: Optional[float] = None
    resolution: Optional[str] = None
    file_size_bytes: Optional[int] = None
    status: str
    thumbnail_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
