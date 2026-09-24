"""
Integration tests for ClipForge core functionality.
Tests are designed to be lightweight and not require heavy dependencies.
"""
import pytest
from unittest.mock import Mock, AsyncMock


class TestCaptionEngine:
    """Test caption engine functionality"""

    def test_srt_format(self):
        """Test SRT subtitle generation"""
        from api.services.captions.caption_engine import (
            CaptionSegment, CaptionLine, SubtitleGenerator,
        )

        segments = [
            CaptionSegment(
                id="test-1",
                start_time=0.0, end_time=3.0,
                language="en",
                lines=[CaptionLine(text="Hello world", start=0.0, end=3.0)]
            )
        ]

        srt = SubtitleGenerator.to_srt(segments)
        assert "1" in srt
        assert "Hello world" in srt
        assert "00:00:00,000" in srt

    def test_vtt_format(self):
        """Test VTT subtitle generation"""
        from api.services.captions.caption_engine import (
            CaptionSegment, CaptionLine, SubtitleGenerator,
        )

        segments = [
            CaptionSegment(
                id="test-1",
                start_time=0.0, end_time=3.0,
                language="en",
                lines=[CaptionLine(text="Hello world", start=0.0, end=3.0)]
            )
        ]

        vtt = SubtitleGenerator.to_vtt(segments)
        assert "WEBVTT" in vtt

    def test_json_format(self):
        """Test JSON subtitle generation"""
        from api.services.captions.caption_engine import (
            CaptionSegment, CaptionLine, SubtitleGenerator,
        )
        import json

        segments = [
            CaptionSegment(
                id="test-1",
                start_time=0.0, end_time=3.0,
                language="en",
                lines=[CaptionLine(text="Hello world", start=0.0, end=3.0)]
            )
        ]

        json_str = SubtitleGenerator.to_json(segments)
        data = json.loads(json_str)
        assert isinstance(data, list)
        assert data[0]["id"] == "test-1"

    def test_style_presets(self):
        """Test predefined caption styles"""
        from api.services.captions.style_engine import StyleEngine

        engine = StyleEngine()
        styles = engine.get_all_styles()
        assert len(styles) >= 8
        assert "clean" in styles
        assert "bold" in styles

    def test_style_creation(self):
        """Test custom style creation"""
        from api.services.captions.style_engine import StyleEngine

        engine = StyleEngine()
        style = engine.create_style("Custom", name="Custom Style", font_size=30)
        assert style["name"] == "Custom Style"
        assert style["font_size"] == 30

    def test_readability_analysis(self):
        """Test caption readability analysis"""
        from api.services.captions.caption_engine import (
            CaptionSegment, CaptionLine, CaptionAnalyzer,
        )

        segments = [
            CaptionSegment(
                id="test-1", start_time=0.0, end_time=3.0, language="en",
                lines=[CaptionLine(text="Hello world test", start=0.0, end=3.0)]
            )
        ]

        analysis = CaptionAnalyzer.analyze_readability(segments)
        assert "total_words" in analysis
        assert "avg_words_per_line" in analysis


class TestCameraPath:
    """Test camera path generation"""

    def test_camera_path_creation(self):
        """Test CameraPath dataclass"""
        from api.services.reframe.reframe_engine import (
            CameraPath, CameraKeyframe, SceneStrategy,
        )

        kf = CameraKeyframe(
            time=0.0, crop_x=0.15, crop_y=0.0, crop_w=0.5, crop_h=1.0,
            zoom=1.0, strategy=SceneStrategy.TRACK,
        )
        path = CameraPath(keyframes=[kf], mode="auto")
        crop = path.get_crop_at_time(0.0)
        assert crop.crop_x == 0.15

    def test_camera_path_interpolation(self):
        """Test smooth interpolation between keyframes"""
        from api.services.reframe.reframe_engine import (
            CameraPath, CameraKeyframe, SceneStrategy,
        )

        kf1 = CameraKeyframe(
            time=0.0, crop_x=0.15, crop_y=0.0, crop_w=0.5, crop_h=1.0,
            zoom=1.0, strategy=SceneStrategy.TRACK,
        )
        kf2 = CameraKeyframe(
            time=10.0, crop_x=0.20, crop_y=0.0, crop_w=0.6, crop_h=1.0,
            zoom=1.05, strategy=SceneStrategy.WIDE,
        )

        path = CameraPath(keyframes=[kf1, kf2], mode="auto")
        crop = path.get_crop_at_time(5.0)
        assert 0.15 <= crop.crop_x <= 0.20

    def test_smoothstep_interpolation(self):
        """Test smoothstep interpolation"""
        from api.services.reframe.reframe_engine import CameraPath

        path = CameraPath()
        t = path._smooth_interpolation(0.5)
        assert 0 < t < 1
        assert t == 0.5  # smoothstep(0.5) = 0.5


class TestAPISchemas:
    """Test API response schemas"""

    def test_api_response(self):
        """Test ApiResponse schema"""
        from api.schemas.common import ApiResponse

        response = ApiResponse(data={"test": "data"}, message="Success")
        assert response.success is True
        assert response.message == "Success"
        assert response.data == {"test": "data"}

    def test_api_response_error(self):
        """Test ErrorResponse schema"""
        from api.schemas.common import ErrorResponse

        response = ErrorResponse(success=False, error="Not found")
        assert response.success is False
        assert response.error == "Not found"


class TestModels:
    """Test database model definitions"""

    def test_caption_style_model(self):
        """Test CaptionStyle model"""
        from api.models.core import CaptionStyle
        assert CaptionStyle.__tablename__ == "caption_styles"
        assert CaptionStyle.font_size.default == 24

    def test_reframe_models(self):
        """Test reframe models"""
        from api.models.reframe import CameraPathData, SpeakerData, FaceDetectionData, ReframeJob
        assert CameraPathData.__tablename__ == "camera_paths"
        assert SpeakerData.__tablename__ == "speaker_data"
        assert FaceDetectionData.__tablename__ == "face_detections"
        assert ReframeJob.__tablename__ == "reframe_jobs"

    def test_core_models(self):
        """Test core models exist"""
        from api.models.core import User, Project, Video, Transcript, Clip
        assert User.__tablename__ == "users"
        assert Project.__tablename__ == "projects"
        assert Video.__tablename__ == "videos"
        assert Transcript.__tablename__ == "transcripts"
        assert Clip.__tablename__ == "clips"


class TestRouterStructure:
    """Test router structure"""

    def test_api_router_exists(self):
        """Test that api_router exists"""
        from api.routers import api_router
        assert api_router is not None
        assert hasattr(api_router, 'include_router')

    def test_api_router_has_routes(self):
        """Test that api_router has routes"""
        from api.routers import api_router
        assert len(api_router.routes) >= 10


class TestConfig:
    """Test configuration"""

    def test_settings_fields(self):
        """Test Settings has all required fields"""
        from dataclasses import fields
        from api.app.config import Settings
        field_names = [f.name for f in fields(Settings)]
        assert "APP_NAME" in field_names
        assert "APP_VERSION" in field_names
        assert "DATABASE_URL" in field_names
        assert "REDIS_URL" in field_names


class TestWorkerTasks:
    """Test worker task definitions"""

    def test_reframe_task_exists(self):
        """Test reframe worker task exists"""
        from worker.tasks import reframe
        assert hasattr(reframe, 'generate_camera_path')
        assert hasattr(reframe, 'render_reframed_clip')

    def test_caption_task_exists(self):
        """Test caption worker task exists"""
        from worker.tasks import captions
        assert hasattr(captions, 'generate_caption_file')
        assert hasattr(captions, 'export_caption_file')

    def test_video_processing_task_exists(self):
        """Test video processing task exists"""
        from worker.tasks import video_processing
        assert hasattr(video_processing, 'process_video')
        assert hasattr(video_processing, 'transcribe_video')


class TestServiceLayer:
    """Test service layer"""

    def test_face_detector_service(self):
        """Test FaceDetectionService exists"""
        from api.services.reframe.face_detector import FaceDetectionService, ReframeService
        assert FaceDetectionService is not None
        assert ReframeService is not None

    def test_caption_engine(self):
        """Test CaptionEngine can be instantiated"""
        from api.services.captions.caption_engine import CaptionEngine
        engine = CaptionEngine()
        assert engine is not None

    def test_style_engine(self):
        """Test StyleEngine can be instantiated"""
        from api.services.captions.style_engine import StyleEngine
        engine = StyleEngine()
        assert engine is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])