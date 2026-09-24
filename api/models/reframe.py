"""
Reframe models — camera path and reframe data models
"""
from sqlalchemy import Column, String, Float, DateTime, JSON, UUID as UUIDColumn
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

from api.core.database import Base


class CameraPathData(Base):
    """Stores generated camera paths for videos"""
    __tablename__ = "camera_paths"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    clip_id = Column(UUID(as_uuid=True), nullable=True)
    aspect_ratio = Column(String(10), nullable=False, default="9:16")
    mode = Column(String(20), nullable=False, default="auto")
    keyframes = Column(JSON, nullable=True)  # List of camera keyframes
    total_keyframes = Column(Integer, nullable=False, default=0)
    comfort_mode = Column(Boolean, nullable=False, default=True)
    static_auto = Column(Boolean, nullable=False, default=True)
    zoom_min = Column(Float, nullable=False, default=1.0)
    zoom_max = Column(Float, nullable=False, default=1.15)
    lost_subject_recovered = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="pending")
    error_message = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class SpeakerData(Base):
    """Stores speaker tracking data"""
    __tablename__ = "speaker_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    speaker_id = Column(String(100), nullable=False)
    frame_number = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False)
    bbox_x = Column(Float, nullable=True)
    bbox_y = Column(Float, nullable=True)
    bbox_w = Column(Float, nullable=True)
    bbox_h = Column(Float, nullable=True)
    activity_level = Column(Float, nullable=False, default=0.0)
    is_active = Column(Boolean, nullable=False, default=False)
    audio_energy = Column(Float, nullable=False, default=0.0)
    mouth_aspect_ratio = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class FaceDetectionData(Base):
    """Stores face detection results per frame"""
    __tablename__ = "face_detections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    frame_number = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False)
    face_count = Column(Integer, nullable=False, default=0)
    faces = Column(JSON, nullable=True)  # List of detected faces
    has_face = Column(Boolean, nullable=False, default=False)
    dominant_face = Column(JSON, nullable=True)  # Primary face data
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ReframeJob(Base):
    """Tracks reframe processing jobs"""
    __tablename__ = "reframe_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    clip_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(20), nullable=False, default="queued")
    mode = Column(String(20), nullable=False, default="auto")
    aspect_ratio = Column(String(10), nullable=False, default="9:16")
    progress = Column(Float, nullable=False, default=0.0)
    total_frames = Column(Integer, nullable=False, default=0)
    processed_frames = Column(Integer, nullable=False, default=0)
    keyframes_generated = Column(Integer, nullable=False, default=0)
    error_message = Column(String(512), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))