# Core database models - remaining tables
from sqlalchemy import Column, String, DateTime, Float, Boolean, JSON, Text, Integer, UUID as UUIDColumn, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

from api.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="active")
    source_type = Column(String(50), nullable=True)
    source_url = Column(String(2048), nullable=True)
    source_path = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(timezone.utc))


class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    original_filename = Column(String(512), nullable=False)
    storage_path = Column(String(1024), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    resolution = Column(String(20), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    status = Column(String(50), nullable=False, default="uploading")
    thumbnail_url = Column(String(1024), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(timezone.utc))


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)
    language = Column(String(10), nullable=True)
    content = Column(JSON, nullable=True)
    full_text = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(timezone.utc))


class ClipCandidate(Base):
    __tablename__ = "clip_candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False, index=True)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    score = Column(Float, nullable=False)
    hook_text = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=True)
    strategy = Column(String(10), nullable=True)
    metadata = Column(JSON, nullable=True)
    selected = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class Clip(Base):
    __tablename__ = "clips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("clip_candidates.id"), nullable=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    hashtags = Column(JSON, nullable=True)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    reframe_path = Column(JSON, nullable=True)
    aspect_ratio = Column(String(10), nullable=False, default="9:16")
    caption_style_id = Column(UUID(as_uuid=True), ForeignKey("caption_styles.id"), nullable=True)
    status = Column(String(50), nullable=False, default="draft")
    output_url = Column(String(1024), nullable=True)
    thumbnail_url = Column(String(1024), nullable=True)
    credits_used = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(timezone.utc))


class CaptionStyle(Base):
    __tablename__ = "caption_styles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    font_family = Column(String(100), nullable=False, default="Inter")
    font_size = Column(Integer, nullable=False, default=24)
    font_color = Column(String(20), nullable=False, default="#FFFFFF")
    background_color = Column(String(20), nullable=False, default="#000000")
    background_opacity = Column(Float, nullable=False, default=0.7)
    outline = Column(Boolean, nullable=False, default=True)
    outline_color = Column(String(20), nullable=False, default="#000000")
    shadow = Column(Boolean, nullable=False, default=False)
    position = Column(String(20), nullable=False, default="bottom")
    max_words_per_line = Column(Integer, nullable=False, default=5)
    animation_type = Column(String(50), nullable=False, default="fade")
    preset_data = Column(JSON, nullable=True)
    is_brand_default = Column(Boolean, nullable=False, default=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class RenderJob(Base):
    __tablename__ = "render_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clip_id = Column(UUID(as_uuid=True), ForeignKey("clips.id"), nullable=False, index=True)
    render_type = Column(String(50), nullable=False, default="preview")
    resolution = Column(String(20), nullable=False, default="1080x1920")
    status = Column(String(50), nullable=False, default="queued")
    progress = Column(Float, nullable=False, default=0)
    estimated_time_seconds = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    attempts = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(timezone.utc))


class RenderOutput(Base):
    __tablename__ = "render_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    render_job_id = Column(UUID(as_uuid=True), ForeignKey("render_jobs.id"), nullable=False, index=True)
    storage_path = Column(String(1024), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    resolution = Column(String(20), nullable=True)
    format = Column(String(20), nullable=False, default="mp4")
    checksum = Column(String(64), nullable=True)
    signed_url = Column(String(1024), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(timezone.utc))


class AIJob(Base):
    __tablename__ = "ai_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(50), nullable=False)
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=False, default=0)
    cost_credits = Column(Float, nullable=False, default=0)
    provider = Column(String(50), nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    job_type = Column(String(50), nullable=False)
    credits_consumed = Column(Float, nullable=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    plan = Column(String(50), nullable=False, default="free")
    credits_total = Column(Float, nullable=False, default=0)
    credits_used = Column(Float, nullable=False, default=0)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    key_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=True)
    permissions = Column(JSON, nullable=True)
    rate_limit = Column(Integer, nullable=False, default=100)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)


class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clip_id = Column(UUID(as_uuid=True), ForeignKey("clips.id"), nullable=False, index=True)
    platform = Column(String(50), nullable=False)
    scheduled_for = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), nullable=False, default="scheduled")
    content = Column(JSON, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
