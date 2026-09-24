"""
Video Processing Pipeline — Phase 2
Handles: upload, URL import, FFmpeg, metadata extraction, audio extraction, transcription
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class VideoStatus(str, Enum):
    UPLOADING = "uploading"
    VALIDATING = "validating"
    EXTRACTING_METADATA = "extracting_metadata"
    EXTRACTING_AUDIO = "extracting_audio"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class VideoMetadata:
    duration_seconds: float
    resolution_width: int
    resolution_height: int
    framerate: float
    audio_sample_rate: int
    audio_channels: int
    codec: str
    format: str
    file_size_bytes: int
    has_video_stream: bool
    has_audio_stream: bool
    bitrate: Optional[str] = None


@dataclass
class ProcessingJob:
    job_id: str
    video_id: str
    stages: list[str]
    current_stage: str = "uploading"
    progress: float = 0.0
    status: str = "queued"
    error: Optional[str] = None
    metadata: VideoMetadata | None = None
    transcript_path: Optional[str] = None
    audio_path: Optional[str] = None
    thumbnail_path: Optional[str] = None


class FFmpegService:
    """FFmpeg wrapper for video processing operations"""

    @staticmethod
    def get_metadata(video_path: str) -> VideoMetadata:
        """Extract video metadata using ffprobe"""
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise ValueError(f"ffprobe failed: {result.stderr}")

        probe = json.loads(result.stdout)
        format_info = probe.get("format", {})
        video_stream = next((s for s in probe.get("streams", []) if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in probe.get("streams", []) if s.get("codec_type") == "audio"), None)

        width = int(video_stream.get("width", 0)) if video_stream else 0
        height = int(video_stream.get("height", 0)) if video_stream else 0
        duration = float(format_info.get("duration", 0))
        framerate = FFmpegService._parse_framerate(video_stream) if video_stream else 0.0

        return VideoMetadata(
            duration_seconds=duration,
            resolution_width=width,
            resolution_height=height,
            framerate=framerate,
            audio_sample_rate=int(audio_stream.get("sample_rate", 0)) if audio_stream else 0,
            audio_channels=int(audio_stream.get("channels", 0)) if audio_stream else 0,
            codec=video_stream.get("codec_name", "unknown") if video_stream else "none",
            format=format_info.get("format_name", "unknown"),
            file_size_bytes=int(format_info.get("size", 0)),
            has_video_stream=video_stream is not None,
            has_audio_stream=audio_stream is not None,
            bitrate=format_info.get("bit_rate"),
        )

    @staticmethod
    def extract_audio(video_path: str, output_path: str) -> str:
        """Extract audio to WAV format for transcription"""
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1",
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise ValueError(f"Audio extraction failed: {result.stderr}")
        return output_path

    @staticmethod
    def extract_audio_flac(video_path: str, output_path: str) -> str:
        """Extract audio to FLAC format for transcription"""
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-acodec", "flac",
            "-ar", "16000", "-ac", "1",
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise ValueError(f"FLAC extraction failed: {result.stderr}")
        return output_path

    @staticmethod
    def extract_thumbnail(video_path: str, output_path: str, timestamp: str = "00:00:05") -> str:
        """Extract a thumbnail frame from video"""
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-ss", timestamp, "-vframes", "1",
            "-q:v", "2", output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.warning(f"Thumbnail extraction failed: {result.stderr}")
        return output_path

    @staticmethod
    def validate_video(video_path: str) -> bool:
        """Validate video file integrity"""
        try:
            FFmpegService.get_metadata(video_path)
            return True
        except Exception:
            return False

    @staticmethod
    def _parse_framerate(stream: dict) -> float:
        """Parse frame rate from stream info"""
        avg_frame_rate = stream.get("avg_frame_rate", "")
        if "/" in avg_frame_rate:
            num, denom = avg_frame_rate.split("/")
            if int(denom) > 0:
                return float(num) / float(denom)
        return float(avg_frame_rate) if avg_frame_rate else 0.0


class YouTubeImporter:
    """Import videos from YouTube URLs using yt-dlp"""

    @staticmethod
    async def download(url: str, output_dir: str) -> dict:
        """Download video from YouTube URL"""
        cmd = [
            "yt-dlp",
            "-f", "bestvideo+bestaudio/best",
            "--merge-output-format", "mp4",
            "-o", os.path.join(output_dir, "%(id)s.%(ext)s"),
            "--no-playlist",
            "--no-write-infojson",
            "--no-write-thumbnail",
            "--no-write-description",
            "--no-write-annotations",
            "--no-sub-languages",
            "--skip-download",
            "--print-json",
            url
        ]
        # First get info
        info_cmd = ["yt-dlp", "--dump-json", "--no-playlist", url]
        info_result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=30)
        if info_result.returncode != 0:
            raise ValueError(f"yt-dlp info failed: {info_result.stderr}")

        info = json.loads(info_result.stdout)

        # Download
        dl_cmd = [
            "yt-dlp",
            "-f", "bestvideo+bestaudio/best",
            "--merge-output-format", "mp4",
            "-o", os.path.join(output_dir, "%(id)s.%(ext)s"),
            "--no-playlist",
            "--no-write-infojson",
            "--no-write-thumbnail",
            "--no-write-description",
            "--no-write-annotations",
            "--no-sub-languages",
            url
        ]
        result = subprocess.run(dl_cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise ValueError(f"yt-dlp download failed: {result.stderr}")

        video_id = info.get("id", "unknown")
        filename = f"{video_id}.mp4"
        filepath = os.path.join(output_dir, filename)

        return {
            "video_id": video_id,
            "filepath": filepath,
            "filename": filename,
            "title": info.get("title", ""),
            "duration": info.get("duration", 0),
            "url": url,
        }


class TranscriptionService:
    """Handles video transcription using faster-whisper or cloud providers"""

    def __init__(self, provider: str = "faster-whisper"):
        self.provider = provider

    async def transcribe(self, audio_path: str, language: str = "auto") -> dict:
        """Transcribe audio and return word-level timestamps"""
        if self.provider == "faster-whisper":
            return await self._transcribe_local(audio_path, language)
        elif self.provider in ("deepgram", "elevenlabs"):
            return await self._transcribe_cloud(audio_path, language)
        else:
            return await self._transcribe_local(audio_path, language)

    async def _transcribe_local(self, audio_path: str, language: str) -> dict:
        """Transcribe using faster-whisper locally"""
        try:
            from faster_whisper import WhisperModel
            model_size = os.environ.get("WHISPER_MODEL", "base")
            model = WhisperModel(model_size, device="cpu", compute_type="int8")

            segments, info = model.transcribe(
                audio_path,
                beam_size=5,
                vad_filter=True,
                language=language if language != "auto" else None,
                word_timestamps=True,
            )

            words = []
            for segment in segments:
                for word in segment.words:
                    words.append({
                        "word": word.word,
                        "start": round(word.start, 3),
                        "end": round(word.end, 3),
                        "probability": round(word.probability, 4),
                    })

            # Build full text
            full_text = " ".join(w["word"] for w in words)

            return {
                "provider": "faster-whisper",
                "language": info.language if info.language else language,
                "language_confidence": round(info.language_probability, 4) if info.language_probability else None,
                "duration": round(info.duration, 3) if info.duration else None,
                "segments": [
                    {
                        "text": s.text,
                        "start": round(s.start, 3),
                        "end": round(s.end, 3),
                        "words": [w for w in words if s.start <= w["start"] <= s.end],
                    }
                    for s in segments
                ],
                "words": words,
                "full_text": full_text,
            }
        except ImportError:
            logger.warning("faster-whisper not installed, using mock transcription")
            return self._mock_transcription(audio_path)
        except Exception as e:
            logger.error(f"Local transcription failed: {str(e)}")
            raise

    async def _transcribe_cloud(self, audio_path: str, language: str) -> dict:
        """Transcribe using Deepgram or ElevenLabs"""
        # Placeholder for cloud provider integration
        # Will be fully implemented in Phase 3
        return self._mock_transcription(audio_path)

    def _mock_transcription(self, audio_path: str) -> dict:
        """Mock transcription for testing without dependencies"""
        return {
            "provider": "mock",
            "language": "en",
            "segments": [
                {"text": "Welcome to this video. This is a test.", "start": 0.0, "end": 5.0, "words": []},
                {"text": "We are testing the transcription pipeline.", "start": 5.0, "end": 10.0, "words": []},
            ],
            "words": [],
            "full_text": "Welcome to this video. This is a test. We are testing the transcription pipeline.",
            "duration": 10.0,
        }


class VideoProcessor:
    """Main video processing orchestrator"""

    def __init__(self):
        self.ffmpeg = FFmpegService()
        self.transcriber = TranscriptionService()
        self.job: Optional[ProcessingJob] = None

    async def process(self, video_path: str, video_id: str) -> ProcessingJob:
        """Process a video through the full pipeline"""
        self.job = ProcessingJob(
            job_id=f"job_{video_id}",
            video_id=video_id,
            stages=[
                "validate", "metadata", "audio", "transcription", "analysis"
            ],
        )

        try:
            # Stage 1: Validate
            self.job.current_stage = "validating"
            self.job.progress = 5.0
            if not self.ffmpeg.validate_video(video_path):
                raise ValueError("Invalid video file")

            # Stage 2: Extract metadata
            self.job.current_stage = "extracting_metadata"
            self.job.progress = 15.0
            self.job.metadata = self.ffmpeg.get_metadata(video_path)
            logger.info(f"Metadata: {self.job.metadata}")

            # Stage 3: Extract audio
            self.job.current_stage = "extracting_audio"
            self.job.progress = 30.0
            audio_dir = tempfile.mkdtemp()
            self.job.audio_path = os.path.join(audio_dir, "audio.wav")
            self.ffmpeg.extract_audio(video_path, self.job.audio_path)

            # Stage 4: Generate thumbnail
            self.job.thumbnail_path = os.path.join(audio_dir, "thumbnail.png")
            self.ffmpeg.extract_thumbnail(video_path, self.job.thumbnail_path)

            # Stage 5: Transcribe
            self.job.current_stage = "transcribing"
            self.job.progress = 50.0
            transcript = await self.transcriber.transcribe(self.job.audio_path)
            self.job.transcript_path = os.path.join(audio_dir, "transcript.json")
            with open(self.job.transcript_path, "w") as f:
                json.dump(transcript, f, indent=2)
            logger.info(f"Transcript: {len(transcript['words'])} words found")

            # Stage 6: Analysis placeholder
            self.job.current_stage = "analyzing"
            self.job.progress = 80.0

            # Complete
            self.job.current_stage = "completed"
            self.job.progress = 100.0
            self.job.status = VideoStatus.COMPLETED.value

        except Exception as e:
            self.job.status = VideoStatus.FAILED.value
            self.job.error = str(e)
            logger.error(f"Processing failed: {str(e)}")

        return self.job


async def process_video_pipeline(video_path: str, video_id: str, project_id: str) -> dict:
    """Entry point for the video processing pipeline"""
    processor = VideoProcessor()
    result = await processor.process(video_path, video_id)
    return {
        "job_id": result.job_id,
        "video_id": result.video_id,
        "status": result.status,
        "progress": result.progress,
        "metadata": result.metadata,
        "transcript_path": result.transcript_path,
        "error": result.error,
    }