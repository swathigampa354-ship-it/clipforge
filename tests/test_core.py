"""
Test configuration for ClipForge
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import pytest_asyncio


@pytest.fixture
def mock_db():
    """Mock database session"""
    db = Mock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def sample_transcript():
    return [
        {"text": "Hello everyone, welcome to this video.", "start": 0.0, "end": 3.5, "confidence": 0.95},
        {"text": "Today we're going to talk about AI.", "start": 3.5, "end": 7.2, "confidence": 0.92},
        {"text": "This is a really interesting topic.", "start": 7.2, "end": 10.0, "confidence": 0.98},
    ]


@pytest.fixture
def sample_video():
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "project_id": "550e8400-e29b-41d4-a716-446655440001",
        "original_filename": "test_video.mp4",
        "duration_seconds": 120.0,
        "status": "uploaded",
    }


@pytest.fixture
def sample_clip_candidates():
    return [
        {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "video_id": "550e8400-e29b-41d4-a716-446655440000",
            "start_time": 5.0,
            "end_time": 12.0,
            "score": 92.5,
            "strategy": "sentence_boundary",
            "confidence": 0.95,
            "selected": True,
        }
    ]


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
                start_time=0.0,
                end_time=3.0,
                language="en",
                lines=[
                    CaptionLine(text="Hello world", start=0.0, end=3.0)
                ],
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
                start_time=0.0,
                end_time=3.0,
                language="en",
                lines=[
                    CaptionLine(text="Hello world", start=0.0, end=3.0)
                ],
            )
        ]

        vtt = SubtitleGenerator.to_vtt(segments)
        assert "WEBVTT" in vtt
        assert "Hello world" in vtt

    def test_json_format(self):
        """Test JSON subtitle generation"""
        from api.services.captions.caption_engine import (
            CaptionSegment, CaptionLine, SubtitleGenerator,
        )

        segments = [
            CaptionSegment(
                id="test-1",
                start_time=0.0,
                end_time=3.0,
                language="en",
                lines=[
                    CaptionLine(text="Hello world", start=0.0, end=3.0)
                ],
            )
        ]

        json_str = SubtitleGenerator.to_json(segments)
        data = __import__("json").loads(json_str)
        assert isinstance(data, list)
        assert data[0]["id"] == "test-1"

    def test_ass_format(self):
        """Test ASS subtitle generation"""
        from api.services.captions.caption_engine import (
            CaptionSegment, CaptionLine, SubtitleGenerator,
        )

        segments = [
            CaptionSegment(
                id="test-1",
                start_time=0.0,
                end_time=3.0,
                language="en",
                lines=[
                    CaptionLine(text="Hello world", start=0.0, end=3.0)
                ],
            )
        ]

        ass = SubtitleGenerator.to_ass(segments)
        assert "WEBVTT" not in ass  # Should have ASS markers
        assert "[Script Info]" in ass
        assert "Hello world" in ass

    def test_style_presets(self):
        """Test predefined caption styles"""
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

    def test_readability_analysis(self):
        """Test caption readability analysis"""
        from api.services.captions.caption_engine import (
            CaptionSegment, CaptionLine, CaptionAnalyzer,
        )

        segments = [
            CaptionSegment(
                id="test-1",
                start_time=0.0,
                end_time=3.0,
                language="en",
                lines=[
                    CaptionLine(text="Hello world test", start=0.0, end=3.0)
                ],
            )
        ]

        analysis = CaptionAnalyzer.analyze_readability(segments)
        assert "total_words" in analysis
        assert "avg_words_per_line" in analysis
        assert "readability_grade" in analysis


class TestCameraPath:
    """Test camera path generation"""

    def test_camera_path_creation(self):
        """Test CameraPath dataclass"""
        from api.services.reframe.reframe_engine import (
            CameraPath, CameraKeyframe, SceneStrategy,
        )

        keyframe = CameraKeyframe(
            time=0.0,
            crop_x=0.15,
            crop_y=0.0,
            crop_w=0.5,
            crop_h=1.0,
            zoom=1.0,
            strategy=SceneStrategy.TRACK,
        )

        path = CameraPath(keyframes=[keyframe], mode="auto")
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

        # Should be interpolated
        assert 0.15 <= crop.crop_x <= 0.20
        assert 1.0 <= crop.zoom <= 1.05


class TestAPIRoutes:
    """Test API route definitions"""

    def test_router_includes_all_routers(self):
        """Test that all routers are included"""
        from api.routers import api_router
        assert api_router is not None

    def test_api_response_schema(self):
        """Test API response schema"""
        from api.schemas.common import ApiResponse

        response = ApiResponse(data={"test": "data"}, message="Success")
        assert response.success is True
        assert response.message == "Success"
        assert response.data == {"test": "data"}


class TestDatabaseModels:
    """Test database model definitions"""

    def test_caption_style_model(self):
        """Test CaptionStyle model"""
        from api.models.core import CaptionStyle
        assert CaptionStyle.__tablename__ == "caption_styles"

    def test_reframe_models(self):
        """Test reframe models"""
        from api.models.reframe import CameraPathData, SpeakerData, FaceDetectionData, ReframeJob
        assert CameraPathData.__tablename__ == "camera_paths"
        assert SpeakerData.__tablename__ == "speaker_data"
        assert FaceDetectionData.__tablename__ == "face_detections"
        assert ReframeJob.__tablename__ == "reframe_jobs"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])