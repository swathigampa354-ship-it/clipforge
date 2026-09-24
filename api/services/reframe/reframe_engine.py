"""
Smart Reframe Engine — Phase 4
Handles: face detection, speaker tracking, camera path generation, 9:16 rendering

License-safe: Uses MediaPipe (Apache 2.0) and OpenCV (Apache 2.0) instead of
YOLOv8 (AGPL-3.0) for face/person detection.
"""
from __future__ import annotations

import json
import logging
import math
import os
import statistics
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Tuple
from uuid import uuid4
from datetime import datetime, timezone

import cv2
import numpy as np

from api.app.config import settings

logger = logging.getLogger(__name__)


class ReframeMode(str, Enum):
    """Reframing strategies"""
    TRACK = "track"       # Single speaker, face tracking
    WIDE = "wide"         # Multiple speakers, wider crop
    GENERAL = "general"   # No face, letterbox
    AUTO = "auto"         # Auto-select strategy per scene
    CENTER = "center"     # Simple center crop, no tracking


class SceneStrategy(str, Enum):
    """Per-scene reframe strategy"""
    TRACK = "TRACK"       # Locked on single face
    WIDE = "WIDE"         # Locked zoomed-out for multiple faces
    GENERAL = "GENERAL"   # Letterbox for no face


@dataclass
class FaceDetection:
    """Detected face data"""
    bbox: Tuple[float, float, float, float]  # (x, y, w, h) normalized 0-1
    confidence: float
    landmarks: Optional[List[Tuple[float, float]]] = None  # (x, y) normalized
    frame_number: int = 0
    timestamp: float = 0.0


@dataclass
class PersonDetection:
    """Detected person data (for screen share, group scenes)"""
    bbox: Tuple[float, float, float, float]
    confidence: float
    class_id: int = 0  # COCO class
    frame_number: int = 0


@dataclass
class SpeakerInfo:
    """Active speaker tracking data"""
    speaker_id: str
    face_id: Optional[str] = None
    bbox: Optional[Tuple[float, float, float, float]] = None
    activity_level: float = 0.0  # Mouth movement, audio energy
    is_active: bool = False
    frame_count: int = 0
    last_active_frame: int = 0


@dataclass
class CameraKeyframe:
    """A single keyframe in the camera path"""
    time: float
    crop_x: float  # Normalized 0-1
    crop_y: float
    crop_w: float
    crop_h: float
    zoom: float = 1.0
    target_speaker: Optional[str] = None
    strategy: SceneStrategy = SceneStrategy.TRACK
    locked: bool = False  # Scene lock — no movement


@dataclass
class CameraPath:
    """Time-varying camera path for reframing"""
    aspect_ratio: str = "9:16"
    keyframes: List[CameraKeyframe] = field(default_factory=list)
    mode: ReframeMode = ReframeMode.AUTO
    target_speakers: List[str] = field(default_factory=list)
    lost_subject_timer: float = 0.0
    current_strategy: SceneStrategy = SceneStrategy.TRACK
    zoom_min: float = 1.0
    zoom_max: float = 1.15
    comfort_mode: bool = True

    def get_crop_at_time(self, time: float) -> CameraKeyframe:
        """Get the crop parameters at a specific time"""
        if not self.keyframes:
            return CameraKeyframe(time=time, crop_x=0.15, crop_y=0.0, crop_w=0.7, crop_h=1.0)

        # Find the two nearest keyframes
        prev_kf = self.keyframes[0]
        next_kf = self.keyframes[-1]

        for kf in self.keyframes:
            if kf.time <= time:
                prev_kf = kf
            if kf.time >= time and next_kf.time > time:
                next_kf = kf
                break

        if prev_kf.time == next_kf.time:
            return prev_kf

        # Interpolate between keyframes
        t = (time - prev_kf.time) / max(next_kf.time - prev_kf.time, 0.001)
        t = max(0, min(1, t))  # Clamp

        # Apply smoothing
        t = self._smooth_interpolation(t)

        return CameraKeyframe(
            time=time,
            crop_x=prev_kf.crop_x + (next_kf.crop_x - prev_kf.crop_x) * t,
            crop_y=prev_kf.crop_y + (next_kf.crop_y - prev_kf.crop_y) * t,
            crop_w=prev_kf.crop_w + (next_kf.crop_w - prev_kf.crop_w) * t,
            crop_h=prev_kf.crop_h + (next_kf.crop_h - prev_kf.crop_h) * t,
            zoom=prev_kf.zoom + (next_kf.zoom - prev_kf.zoom) * t,
            target_speaker=next_kf.target_speaker if t > 0.5 else prev_kf.target_speaker,
            strategy=next_kf.strategy,
        )

    def _smooth_interpolation(self, t: float) -> float:
        """Smoothstep interpolation for camera movement"""
        return t * t * (3 - 2 * t)


class FaceDetector:
    """Face detection using MediaPipe Face Mesh (Apache 2.0)"""

    def __init__(self):
        self.face_mesh = None
        self._initialize()

    def _initialize(self):
        """Initialize MediaPipe Face Mesh"""
        try:
            import mediapipe as mp
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                max_num_faces=4,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            logger.info("MediaPipe Face Mesh initialized")
        except ImportError:
            logger.warning("MediaPipe not installed. Using OpenCV Haar cascades as fallback.")
            self.face_mesh = None
            self._init_opencv_fallback()

    def _init_opencv_fallback(self):
        """Fallback face detection using OpenCV"""
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def detect_faces(self, frame: np.ndarray) -> List[FaceDetection]:
        """Detect faces in a frame"""
        faces = []

        if self.face_mesh is not None:
            faces = self._detect_with_mediapipe(frame)
        elif hasattr(self, 'face_cascade'):
            faces = self._detect_with_opencv(frame)

        return faces

    def _detect_with_mediapipe(self, frame: np.ndarray) -> List[FaceDetection]:
        """Detect faces using MediaPipe Face Mesh"""
        import mediapipe as mp

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        faces = []
        if results.multi_face_landmarks:
            h, w = frame.shape[:2]
            for i, landmarks in enumerate(results.multi_face_landmarks):
                # Get bounding box from landmarks
                x_min, y_min, x_max, y_max = 1.0, 1.0, 0.0, 0.0
                landmarks_list = []

                for lm in landmarks.landmark:
                    x, y = int(lm.x * w), int(lm.y * h)
                    landmarks_list.append((lm.x, lm.y))
                    x_min = min(x_min, lm.x)
                    y_min = min(y_min, lm.y)
                    x_max = max(x_max, lm.x)
                    y_max = max(y_max, lm.y)

                # Calculate mouth aspect ratio for activity detection
                mar = self._calculate_mar(landmarks_list)

                bbox = (
                    max(0, x_min),
                    max(0, y_min),
                    min(1.0, x_max - x_min),
                    min(1.0, y_max - y_min),
                )

                faces.append(FaceDetection(
                    bbox=bbox,
                    confidence=0.9,
                    landmarks=landmarks_list,
                    frame_number=0,
                    timestamp=0.0,
                ))

        return faces

    def _detect_with_opencv(self, frame: np.ndarray) -> List[FaceDetection]:
        """Fallback face detection using OpenCV Haar cascades"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )

        h, w = frame.shape[:2]
        result = []
        for (x, y, fw, fh) in faces:
            result.append(FaceDetection(
                bbox=(x/w, y/h, fw/w, fh/h),
                confidence=0.8,
                frame_number=0,
                timestamp=0.0,
            ))
        return result

    def _calculate_mar(self, landmarks: List[Tuple[float, float]]) -> float:
        """Calculate Mouth Aspect Ratio for activity detection"""
        if len(landmarks) < 60:
            return 0.0

        # MediaPipe face mesh landmark indices for mouth
        # 61, 62, 63, 64, 65, 66 - mouth area
        try:
            left_lip = landmarks[61]
            right_lip = landmarks[66]
            top_lip = landmarks[62]
            bottom_lip = landmarks[64]

            lip_width = ((left_lip[0] - right_lip[0]) ** 2 +
                        (left_lip[1] - right_lip[1]) ** 2) ** 0.5
            lip_height = ((top_lip[0] - bottom_lip[0]) ** 2 +
                         (top_lip[1] - bottom_lip[1]) ** 2) ** 0.5

            return lip_height / max(lip_width, 0.001)
        except (IndexError, KeyError):
            return 0.0

    def detect(self, frame: np.ndarray, timestamp: float = 0.0) -> List[FaceDetection]:
        """Main detection interface"""
        faces = self.detect_faces(frame)
        for face in faces:
            face.timestamp = timestamp
        return faces


class SpeakerTracker:
    """Active speaker detection using face activity + audio energy"""

    def __init__(self, mar_threshold: float = 0.03):
        self.mar_threshold = mar_threshold
        self.speakers: dict[str, SpeakerInfo] = {}
        self.current_active_speaker: Optional[str] = None
        self.face_detector = FaceDetector()

    def update(
        self,
        faces: List[FaceDetection],
        audio_energy: float = 0.0,
        frame_number: int = 0,
    ) -> Optional[str]:
        """Update speaker tracking and return the active speaker ID"""
        active_speakers = []

        for face in faces:
            speaker_id = f"face_{int(face.bbox[0] * 1000)}_{int(face.bbox[1] * 1000)}"

            # Calculate activity level based on MAR and audio energy
            mar = face.landmarks and self._calculate_mar_from_landmarks(face.landmarks)
            activity = max(mar if mar else 0, audio_energy * 0.1)

            if speaker_id not in self.speakers:
                self.speakers[speaker_id] = SpeakerInfo(
                    speaker_id=speaker_id,
                    face_id=speaker_id,
                    bbox=face.bbox,
                    activity_level=activity,
                    frame_count=1,
                    last_active_frame=frame_number,
                )
            else:
                speaker = self.speakers[speaker_id]
                speaker.activity_level = activity * 0.3 + speaker.activity_level * 0.7  # EMA
                speaker.last_active_frame = frame_number
                speaker.frame_count += 1
                speaker.bbox = face.bbox

            if activity > self.mar_threshold:
                active_speakers.append(speaker_id)

        # Determine active speaker
        if active_speakers:
            # Pick the most active speaker
            active_speakers.sort(
                key=lambda sid: self.speakers[sid].activity_level, reverse=True
            )
            self.current_active_speaker = active_speakers[0]
        elif self._has_recent_speakers(frame_number):
            # Hold the last active speaker briefly
            pass
        else:
            self.current_active_speaker = None

        return self.current_active_speaker

    def _calculate_mar_from_landmarks(self, landmarks: List[Tuple[float, float]]) -> float:
        """Calculate MAR from landmarks"""
        return FaceDetector()._calculate_mar(landmarks)

    def _has_recent_speakers(self, frame_number: int, hold_frames: int = 90) -> bool:
        """Check if there are recently active speakers"""
        for speaker in self.speakers.values():
            if frame_number - speaker.last_active_frame < hold_frames:
                return True
        return False

    def get_active_speaker_bbox(self) -> Optional[Tuple[float, float, float, float]]:
        """Get bounding box of the active speaker"""
        if self.current_active_speaker and self.current_active_speaker in self.speakers:
            return self.speakers[self.current_active_speaker].bbox
        return None

    def reset(self):
        """Reset speaker tracker state"""
        self.speakers.clear()
        self.current_active_speaker = None


class CameraPathGenerator:
    """Generates time-varying camera paths for reframing"""

    def __init__(self, mode: ReframeMode = ReframeMode.AUTO):
        self.mode = mode
        self.comfort_mode = True
        self.zoom_min = 1.0
        self.zoom_max = 1.15
        self.scene_lock_threshold = 0.30
        self.zoom_lock = True

    def generate_path(
        self,
        faces_history: List[List[FaceDetection]],
        fps: float,
        duration: float,
        active_speakers: Optional[List[str]] = None,
    ) -> CameraPath:
        """Generate a complete camera path for a video"""
        path = CameraPath(mode=self.mode)

        # Analyze frames to determine scene strategy per segment
        scene_changes = self._detect_scene_changes(faces_history)
        segment_duration = duration / len(scene_changes) if scene_changes else duration / 10

        for i, scene_idx in enumerate(scene_changes):
            time = i * segment_duration
            strategy = self._determine_strategy(
                faces_history, time, scene_idx, active_speakers
            )
            crop = self._calculate_crop(
                faces_history, time, strategy, active_speakers
            )

            keyframe = CameraKeyframe(
                time=time,
                crop_x=crop[0],
                crop_y=crop[1],
                crop_w=crop[2],
                crop_h=crop[3],
                zoom=self._calculate_zoom(crop),
                strategy=strategy,
                locked=self._is_scene_locked(time, scene_changes),
            )
            path.keyframes.append(keyframe)

        return path

    def _detect_scene_changes(self, faces_history: List[List[FaceDetection]]) -> List[int]:
        """Detect scene boundaries"""
        scene_changes = [0]  # Always start at frame 0

        if len(faces_history) < 10:
            return scene_changes

        # Detect changes in face count or position
        prev_count = len(faces_history[0])
        prev_center_x = self._average_x(faces_history[0])

        for i in range(10, len(faces_history), 10):
            current_count = len(faces_history[i])
            current_center_x = self._average_x(faces_history[i])

            # Scene change if face count changes significantly or center moves
            if abs(current_count - prev_count) > 1 or abs(current_center_x - prev_center_x) > 0.2:
                scene_changes.append(i)
                prev_count = current_count
                prev_center_x = current_center_x

        return scene_changes if len(scene_changes) > 1 else [0, len(faces_history) - 1]

    def _determine_strategy(
        self,
        faces_history: List[List[FaceDetection]],
        time: float,
        frame_idx: int,
        active_speakers: Optional[List[str]],
    ) -> SceneStrategy:
        """Determine the reframe strategy for a scene"""
        faces = faces_history[min(frame_idx, len(faces_history) - 1)]

        if len(faces) == 0:
            return SceneStrategy.GENERAL
        elif len(faces) == 1:
            return SceneStrategy.TRACK
        elif len(faces) >= 2:
            return SceneStrategy.WIDE
        else:
            return SceneStrategy.TRACK

    def _calculate_crop(
        self,
        faces_history: List[List[FaceDetection]],
        time: float,
        strategy: SceneStrategy,
        active_speakers: Optional[List[str]],
    ) -> Tuple[float, float, float, float]:
        """Calculate crop parameters for a given time"""
        frame_idx = min(int(time * 30), len(faces_history) - 1)  # Assume 30fps
        faces = faces_history[frame_idx] if frame_idx < len(faces_history) else []

        if strategy == SceneStrategy.TRACK and faces:
            # Center crop on the face
            center_x = self._average_x(faces)
            center_y = self._average_y(faces)
            # 9:16 crop centered on face
            return (
                max(0, min(0.85, center_x - 0.25)),  # x
                0.0,  # y (full height)
                0.5,  # width (50% of frame = 9:16)
                1.0,  # height (full height)
            )
        elif strategy == SceneStrategy.WIDE and faces:
            # Wider crop showing multiple faces
            return (
                self._average_x(faces) - 0.35,
                0.0,
                0.7,
                1.0,
            )
        else:
            # Center crop with letterbox
            return (0.15, 0.0, 0.7, 1.0)

    def _calculate_zoom(self, crop: Tuple[float, float, float, float]) -> float:
        """Calculate zoom level based on crop"""
        width = crop[2]
        if width < 0.4:
            return 1.15  # Tight zoom
        elif width < 0.55:
            return 1.05  # Medium zoom
        return 1.0  # Normal

    def _is_scene_locked(self, time: float, scene_changes: List[int]) -> bool:
        """Check if current scene should be locked (static camera)"""
        if not self.comfort_mode or not self.zoom_lock:
            return False

        # Lock camera during stable scenes
        for change_point in scene_changes:
            if abs(time - change_point) < 2.0:  # 2 seconds after scene change
                return False
        return True

    @staticmethod
    def _average_x(faces: List[FaceDetection]) -> float:
        """Calculate average X center of faces"""
        if not faces:
            return 0.5
        return statistics.mean([face.bbox[0] + face.bbox[2] / 2 for face in faces])

    @staticmethod
    def _average_y(faces: List[FaceDetection]) -> float:
        """Calculate average Y center of faces"""
        if not faces:
            return 0.5
        return statistics.mean([face.bbox[1] + face.bbox[3] / 2 for face in faces])


class LostSubjectRecovery:
    """Handles recovery when the tracked subject is lost"""

    def __init__(self, hold_frames: int = 90, drift_rate: float = 0.05):
        self.hold_frames = hold_frames
        self.drift_rate = drift_rate
        self.last_known_center: Optional[Tuple[float, float]] = None
        self.frames_since_last_seen = 0

    def update(self, face_detected: bool, current_center: Optional[Tuple[float, float]]) -> dict:
        """Update recovery state"""
        action = {"drift_x": 0.0, "drift_y": 0.0, "zoom_adjustment": 0.0}

        if face_detected and current_center:
            self.last_known_center = current_center
            self.frames_since_last_seen = 0
            action["drift_x"] = 0.0
            action["drift_y"] = 0.0
        else:
            self.frames_since_last_seen += 1

            if self.frames_since_last_seen < self.hold_frames:
                # Hold at last known position
                if self.last_known_center:
                    action["drift_x"] = 0.0
                    action["drift_y"] = 0.0
            else:
                # Gradually drift back to center
                action["drift_x"] = (0.5 - self.last_known_center[0]) * self.drift_rate if self.last_known_center else 0.0
                action["drift_y"] = (0.5 - self.last_known_center[1]) * self.drift_rate if self.last_known_center else 0.0
                action["zoom_adjustment"] = 0.05  # Zoom out slightly

        return action

    def needs_recovery(self) -> bool:
        """Check if recovery is needed"""
        return self.frames_since_last_seen > self.hold_frames

    def reset(self):
        """Reset recovery state"""
        self.last_known_center = None
        self.frames_since_last_seen = 0


class ReframeEngine:
    """Main reframing orchestrator"""

    def __init__(self, mode: ReframeMode = ReframeMode.AUTO):
        self.mode = mode
        self.face_detector = FaceDetector()
        self.speaker_tracker = SpeakerTracker()
        self.camera_generator = CameraPathGenerator(mode=mode)
        self.recovery = LostSubjectRecovery()
        self.path: Optional[CameraPath] = None

    def generate_reframe_path(
        self,
        video_path: str,
        fps: float = 30.0,
        duration: float = 0.0,
    ) -> CameraPath:
        """Generate complete reframe path for a video"""
        # Sample frames at intervals
        sample_interval = max(1, int(fps * 0.5))  # Sample every 0.5 seconds
        faces_history: List[List[FaceDetection]] = []

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_duration = duration or total_frames / fps
        frame_number = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_number % sample_interval == 0:
                    faces = self.face_detector.detect(frame, timestamp=frame_number / fps)
                    faces_history.append(faces)

                    # Update speaker tracker
                    if faces:
                        audio_energy = 0.0  # Would come from audio analysis
                        self.speaker_tracker.update(faces, audio_energy, frame_number)

                frame_number += 1

                if frame_number % 100 == 0:
                    logger.info(f"Processing frame {frame_number}/{total_frames}")
        finally:
            cap.release()

        # Generate camera path
        active_speakers = [self.speaker_tracker.current_active_speaker] if self.speaker_tracker.current_active_speaker else None
        self.path = self.camera_generator.generate_path(
            faces_history, fps, video_duration, active_speakers
        )

        return self.path

    def render_reframed_clip(
        self,
        video_path: str,
        output_path: str,
        camera_path: CameraPath,
        aspect_ratio: str = "9:16",
    ) -> str:
        """Render a reframed clip using FFmpeg"""
        crop_params = camera_path.get_crop_at_time(0)

        # Build FFmpeg filter for cropping
        x = int(crop_params.crop_x * 100)
        y = int(crop_params.crop_y * 100)
        w = int(crop_params.crop_w * 100)
        h = int(crop_params.crop_h * 100)

        # Get video dimensions
        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        # Calculate crop coordinates in pixels
        crop_w_px = int(width * crop_params.crop_w)
        crop_h_px = int(height * crop_params.crop_h)
        crop_x_px = int(width * crop_params.crop_x)
        crop_y_px = int(height * crop_params.crop_y)

        # Ensure valid crop
        crop_w_px = max(1, min(crop_w_px, width - crop_x_px))
        crop_h_px = max(1, min(crop_h_px, height - crop_y_px))

        # FFmpeg command for cropping and scaling to target aspect ratio
        target_width, target_height = self._get_target_resolution(aspect_ratio)

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf",
            f"crop={crop_w_px}:{crop_h_px}:{crop_x_px}:{crop_y_px},"
            f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,"
            f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black",
            "-c:v", "libx264",
            "-crf", str(settings.CLIPPYME_X264_CRF),
            "-preset", settings.CLIPPYME_X264_PRESET,
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise ValueError(f"FFmpeg reframe failed: {result.stderr}")

        return output_path

    def _get_target_resolution(self, aspect_ratio: str) -> Tuple[int, int]:
        """Get target resolution for aspect ratio"""
        if aspect_ratio == "9:16":
            return 1080, 1920
        elif aspect_ratio == "1:1":
            return 1080, 1080
        elif aspect_ratio == "16:9":
            return 1920, 1080
        return 1080, 1920


import subprocess  # Only needed for render_reframed_clip


class SmartCropEngine:
    """Intelligent cropping that adapts per-frame"""

    def __init__(self):
        self.reframe = ReframeEngine()
        self.comfort_mode = True
        self.static_auto = True
        self.smoothing_method = "savgol"

    def process_frame(self, frame: np.ndarray, time: float) -> dict:
        """Process a single frame for cropping"""
        faces = self.reframe.face_detector.detect(frame, timestamp=time)

        if not faces:
            return {
                "crop": (0.15, 0.0, 0.7, 1.0),
                "strategy": SceneStrategy.GENERAL,
                "zoom": 1.0,
                "active_speaker": None,
            }

        active_speaker = self.reframe.speaker_tracker.update(faces, frame_number=int(time * 30))
        bbox = self.reframe.speaker_tracker.get_active_speaker_bbox()

        if bbox:
            center_x = bbox[0] + bbox[2] / 2
            center_y = bbox[1] + bbox[3] / 2
            return {
                "crop": (max(0, center_x - 0.25), 0.0, 0.5, 1.0),
                "strategy": SceneStrategy.TRACK,
                "zoom": 1.05,
                "active_speaker": active_speaker,
            }

        return {
            "crop": (0.15, 0.0, 0.7, 1.0),
            "strategy": SceneStrategy.GENERAL,
            "zoom": 1.0,
            "active_speaker": None,
        }

    def generate_camera_path(
        self,
        video_path: str,
        fps: float,
        duration: float,
    ) -> CameraPath:
        """Generate complete camera path for a video"""
        return self.reframe.generate_reframe_path(video_path, fps, duration)