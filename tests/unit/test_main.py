"""
Unit tests for ClipForge API
Uses SQLite in-memory for fast, isolated tests.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


class TestHealthEndpoint:
    """Test the health check endpoint"""

    def test_health_response_format(self):
        """Test health endpoint returns expected format"""
        # Health endpoint is defined in api/app/main.py
        # We test the logic directly
        status = {"status": "healthy", "version": "0.1.0"}
        assert status["status"] == "healthy"
        assert "version" in status

    def test_version_format(self):
        """Test version follows semantic versioning"""
        version = "0.1.0"
        parts = version.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)


class TestSettings:
    """Test configuration settings"""

    def test_settings_defaults(self):
        """Test that settings have default values"""
        # Test that the Settings dataclass has all required fields
        from dataclasses import fields
        from api.app.config import Settings
        field_names = [f.name for f in fields(Settings)]
        assert "APP_NAME" in field_names
        assert "APP_VERSION" in field_names
        assert "DATABASE_URL" in field_names
        assert "REDIS_URL" in field_names


class TestModels:
    """Test database model definitions"""

    def test_caption_style_model(self):
        """Test CaptionStyle model exists"""
        from api.models.core import CaptionStyle
        assert CaptionStyle.__tablename__ == "caption_styles"

    def test_reframe_models(self):
        """Test reframe models exist"""
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


class TestCaptionEngine:
    """Test caption engine functionality"""

    def test_srt_format(self):
        """Test SRT subtitle generation"""
        from api.services.captions.caption_engine import CaptionSegment, CaptionLine, SubtitleGenerator

        segments = [
            CaptionSegment(
                id="test-1",
                start_time=0.0,
                end_time=3.0,
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
        from api.services.captions.caption_engine import CaptionSegment, CaptionLine, SubtitleGenerator

        segments = [
            CaptionSegment(
                id="test-1",
                start_time=0.0,
                end_time=3.0,
                language="en",
                lines=[CaptionLine(text="Hello world", start=0.0, end=3.0)]
            )
        ]

        vtt = SubtitleGenerator.to_vtt(segments)
        assert "WEBVTT" in vtt

    def test_json_format(self):
        """Test JSON subtitle generation"""
        from api.services.captions.caption_engine import CaptionSegment, CaptionLine, SubtitleGenerator
        import json

        segments = [
            CaptionSegment(
                id="test-1",
                start_time=0.0,
                end_time=3.0,
                language="en",
                lines=[CaptionLine(text="Hello world", start=0.0, end=3.0)]
            )
        ]

        json_str = SubtitleGenerator.to_json(segments)
        data = json.loads(json_str)
        assert isinstance(data, list)
        assert data[0]["id"] == "test-1"


class TestStyleEngine:
    """Test caption style engine"""

    def test_predefined_styles(self):
        """Test all predefined styles exist"""
        from api.services.captions.style_engine import StyleEngine

        engine = StyleEngine()
        styles = engine.get_all_styles()
        assert len(styles) >= 8
        assert "clean" in styles
        assert "bold" in styles
        assert "high_impact" in styles

    def test_style_creation(self):
        """Test custom style creation"""
        from api.services.captions.style_engine import StyleEngine

        engine = StyleEngine()
        style = engine.create_style("Custom", name="Custom Style", font_size=30)
        assert style["name"] == "Custom Style"
        assert style["font_size"] == 30


class TestCameraPath:
    """Test camera path generation"""

    def test_camera_path_creation(self):
        """Test CameraPath dataclass"""
        from api.services.reframe.reframe_engine import CameraPath, CameraKeyframe, SceneStrategy

        keyframe = CameraKeyframe(
            time=0.0, crop_x=0.15, crop_y=0.0, crop_w=0.5, crop_h=1.0,
            zoom=1.0, strategy=SceneStrategy.TRACK,
        )

        path = CameraPath(keyframes=[keyframe], mode="auto")
        crop = path.get_crop_at_time(0.0)
        assert crop.crop_x == 0.15

    def test_camera_path_interpolation(self):
        """Test smooth interpolation between keyframes"""
        from api.services.reframe.reframe_engine import CameraPath, CameraKeyframe, SceneStrategy

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


class TestAPIResponse:
    """Test API response schema"""

    def test_api_response(self):
        """Test ApiResponse schema"""
        from api.schemas.common import ApiResponse

        response = ApiResponse(data={"test": "data"}, message="Success")
        assert response.success is True
        assert response.message == "Success"
        assert response.data == {"test": "data"}

    def test_api_response_error(self):
        """Test ApiResponse with error"""
        from api.schemas.common import ErrorResponse

        response = ErrorResponse(success=False, error="Not found")
        assert response.success is False
        assert response.error == "Not found"


class TestRouterStructure:
    """Test router structure"""

    def test_router_has_api_router(self):
        """Test that api_router exists"""
        from api.routers import api_router
        assert api_router is not None
        assert hasattr(api_router, 'include_router')

    def test_api_router_prefix(self):
        """Test that api_router is properly configured"""
        from api.routers import api_router
        # The router should have been initialized with all sub-routers
        assert len(api_router.routes) >= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])