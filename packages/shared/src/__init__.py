# Shared types and configuration for ClipForge packages
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from uuid import UUID


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class VideoStatus(str, Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ClipStatus(str, Enum):
    DRAFT = "draft"
    RENDERING = "rendering"
    RENDERED = "rendered"
    FAILED = "failed"


class AspectRatio(str, Enum):
    RATIO_9_16 = "9:16"
    RATIO_1_1 = "1:1"
    RATIO_16_9 = "16:9"


@dataclass
class VideoMetrics:
    duration_seconds: float
    resolution: str
    file_size_bytes: int
    fps: int = 30
    audio_sample_rate: int = 16000


@dataclass
class ClipCandidateData:
    start_time: float
    end_time: float
    score: float
    hook_text: Optional[str] = None
    category: Optional[str] = None
    confidence: Optional[float] = None
    strategy: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ReframePath:
    aspect_ratio: str
    keyframes: list[dict] = field(default_factory=list)
    track_target: Optional[str] = None
    mode: str = "track"
    zoom_range: dict = field(default_factory=lambda: {"min": 1.0, "max": 1.15})


@dataclass
class CaptionStyleData:
    name: str
    font_family: str = "Inter"
    font_size: int = 24
    font_color: str = "#FFFFFF"
    background_color: str = "#000000"
    background_opacity: float = 0.7
    outline: bool = True
    outline_color: str = "#000000"
    shadow: bool = False
    position: str = "bottom"
    max_words_per_line: int = 5
    animation_type: str = "fade"
    preset_data: dict = field(default_factory=dict)
