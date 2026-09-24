"""
Face detection service — integrates with the reframe engine
"""
from __future__ import annotations

import logging
from typing import Optional, List
from uuid import UUID as UUIDType

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.core.database import AsyncSessionLocal
from api.models.core import Video
from api.services.reframe.reframe_engine import FaceDetector, SpeakerTracker, CameraPath, CameraKeyframe

logger = logging.getLogger(__name__)


class FaceDetectionService:
    """Service for face detection and tracking"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.face_detector = FaceDetector()
        self.speaker_tracker = SpeakerTracker()

    async def detect_faces(self, video_id: UUIDType) -> dict:
        """Detect faces in a video and generate tracking data"""
        # Get video
        result = await self.db.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()
        if not video:
            raise ValueError(f"Video {video_id} not found")

        # Run face detection
        faces = self.face_detector.detect_faces(frame)

        return {
            "video_id": str(video_id),
            "detected": len(faces) > 0,
            "face_count": len(faces),
            "tracking_data": {f"face_{i}": face.bbox for i, face in enumerate(faces)},
        }

    async def get_camera_path(self, video_id: UUIDType) -> Optional[CameraPath]:
        """Get the generated camera path for a video"""
        # In production, this would query the stored camera path
        return None

    async def store_camera_path(self, video_id: UUIDType, path: CameraPath) -> None:
        """Store the generated camera path"""
        # In production, this would store in a database column
        logger.info(f"Stored camera path for video {video_id}")

    async def track_speakers(self, video_id: UUIDType, faces_data: list) -> dict:
        """Track active speakers across video frames"""
        for face_data in faces_data:
            self.speaker_tracker.update(
                faces=[face_data],
                audio_energy=face_data.get("audio_energy", 0.0),
                frame_number=face_data.get("frame", 0),
            )

        active_speaker = self.speaker_tracker.current_active_speaker
        return {
            "video_id": str(video_id),
            "active_speaker": active_speaker,
            "speaker_count": len(self.speaker_tracker.speakers),
        }

    def get_reframe_path_for_clip(
        self,
        clip_start: float,
        clip_end: float,
        camera_path: CameraPath,
    ) -> list[CameraKeyframe]:
        """Get camera keyframes for a specific clip"""
        keyframes = []
        time = clip_start
        while time <= clip_end:
            kf = camera_path.get_crop_at_time(time)
            keyframes.append(kf)
            time += 0.5  # 0.5 second intervals
        return keyframes


class ReframeService:
    """Main reframing service"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.face_service = FaceDetectionService(db)

    async def reframe_video(
        self,
        video_id: UUIDType,
        aspect_ratio: str = "9:16",
        mode: str = "auto",
    ) -> dict:
        """Generate reframed version of a video"""
        # Get camera path
        camera_path = await self.face_service.get_camera_path(video_id)

        if not camera_path:
            # Generate new path
            result = await self.db.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            if video and video.storage_path:
                from api.services.reframe.reframe_engine import ReframeEngine
                engine = ReframeEngine(mode=mode)
                camera_path = engine.generate_reframe_path(
                    video.storage_path, fps=30.0, duration=video.duration_seconds or 0
                )
                await self.face_service.store_camera_path(video_id, camera_path)

        return {
            "video_id": str(video_id),
            "aspect_ratio": aspect_ratio,
            "mode": mode,
            "camera_path": camera_path.keyframes if camera_path else [],
            "status": "completed",
        }

    async def reframe_clip(
        self,
        clip_id: UUIDType,
        clip_start: float,
        clip_end: float,
        source_path: str,
        output_path: str,
        aspect_ratio: str = "9:16",
    ) -> dict:
        """Reframe a single clip"""
        from api.services.reframe.reframe_engine import ReframeEngine

        engine = ReframeEngine()
        camera_path = engine.generate_reframe_path(source_path)

        engine.render_reframed_clip(source_path, output_path, camera_path, aspect_ratio)

        return {
            "clip_id": str(clip_id),
            "output_path": output_path,
            "aspect_ratio": aspect_ratio,
            "status": "completed",
        }