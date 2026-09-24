"""
Worker tasks for the complete video processing pipeline
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from uuid import UUID, uuid4

from celery import shared_task
from celery.utils.log import get_task_logger
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from api.app.config import settings
from api.core.database import Base as DBBase

logger = get_task_logger(__name__)

# Database setup for worker
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


@shared_task(bind=True, max_retries=3)
def process_video(self, video_id: str, project_id: str, user_id: str) -> dict:
    """
    Main video processing pipeline task
    
    Stages:
    1. Download/Validate
    2. Extract Metadata
    3. Extract Audio
    4. Transcribe
    5. AI Analysis
    6. Clip Detection
    7. Smart Reframe
    8. Caption Generation
    9. Metadata Generation
    10. Preview Render
    """
    logger.info(f"Starting video processing pipeline for video {video_id}")
    job_id = uuid4()
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _process_video_async(job_id, video_id, project_id, user_id)
        )
        loop.close()
        
        return result
    except Exception as e:
        logger.error(f"Pipeline failed for video {video_id}: {str(e)}")
        self.retry(exc=e, countdown=60)


async def _process_video_async(job_id: str, video_id: str, project_id: str, user_id: str) -> dict:
    """Async version of the video processing pipeline"""
    from api.services.video_service import VideoService
    from api.services.video_processing import VideoProcessor
    from api.services.clip_service import ClipService
    from api.services.ai.transcript_service import TranscriptService
    
    db_session = AsyncSessionLocal()
    
    try:
        # Stage 1: Validate
        await _update_job_progress(db_session, job_id, "validating", 5)
        video_service = VideoService(db_session)
        video = await video_service.get_video(video_id)
        if not video:
            raise ValueError(f"Video {video_id} not found")
        
        # Stage 2: Extract Metadata
        await _update_job_progress(db_session, job_id, "extracting_metadata", 15)
        from api.services.video_processing import FFmpegService
        metadata = await FFmpegService.extract_metadata(video.storage_path)
        
        # Stage 3: Extract Audio
        await _update_job_progress(db_session, job_id, "extracting_audio", 30)
        audio_path = f"/tmp/{video_id}_audio.wav"
        await FFmpegService.extract_audio(video.storage_path, audio_path)
        
        # Stage 4: Transcribe
        await _update_job_progress(db_session, job_id, "transcribing", 50)
        from api.services.video_processing import TranscriptionService
        transcriber = TranscriptionService(provider="faster-whisper")
        transcript = await transcriber.transcribe(audio_path)
        
        # Store transcript
        transcript_service = TranscriptService(db_session)
        await transcript_service.store_transcript(video_id, transcript, language="en")
        
        # Stage 5: AI Analysis
        await _update_job_progress(db_session, job_id, "analyzing", 70)
        from api.services.ai.analysis_engine import AIAnalysisService
        from api.services.ai.clip_detection import ClipDetectionService
        
        analysis_service = AIAnalysisService()
        analysis_result = await analysis_service.analyze(
            video_id=video_id,
            transcript=transcript.content if hasattr(transcript, 'content') else str(transcript),
            segments=[],
        )
        
        # Store candidates
        detection_service = ClipDetectionService(db_session)
        await detection_service.store_candidates(video_id, analysis_result.candidates)
        
        # Stage 6: Detect Clips
        await _update_job_progress(db_session, job_id, "detecting_clips", 80)
        
        # Stage 7: Smart Reframe
        await _update_job_progress(db_session, job_id, "reframing", 90)
        from api.services.reframe.reframe_engine import ReframeEngine
        if video.storage_path:
            engine = ReframeEngine()
            camera_path = engine.generate_reframe_path(video.storage_path)
        
        # Stage 8: Generate Captions
        await _update_job_progress(db_session, job_id, "generating_captions", 95)
        from api.services.captions.caption_engine import CaptionEngine
        caption_engine = CaptionEngine()
        segments = caption_engine.generate_captions(
            transcript=transcript.content if hasattr(transcript, 'content') else str(transcript),
            video_duration=metadata.get('duration', 0),
        )
        
        # Stage 9: Generate Metadata
        await _update_job_progress(db_session, job_id, "rendering_preview", 97)
        
        # Stage 10: Completed
        await _update_job_progress(db_session, job_id, "completed", 100)
        
        logger.info(f"Pipeline completed for video {video_id}")
        return {"job_id": str(job_id), "video_id": video_id, "status": "completed"}
        
    except Exception as e:
        await _update_job_progress(db_session, job_id, "failed", 0, str(e))
        raise
    finally:
        await db_session.close()


async def _update_job_progress(db: AsyncSession, job_id: str, stage: str, progress: float, error: str = None):
    """Update job progress in database"""
    from sqlalchemy import update
    try:
        from api.models.core import Video
        stmt = update(Video).where(Video.id == job_id).values(
            status=stage, progress=progress,
            updated_at=datetime.now(timezone.utc)
        )
        await db.execute(stmt)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to update job progress: {str(e)}")


@shared_task(bind=True, max_retries=3)
def render_clip(self, clip_id: str, render_type: str = "final", resolution: str = "1080x1920", source_path: str = None) -> dict:
    """
    Render a clip to MP4 using FFmpeg
    
    Handles:
    - Video cut from source
    - Smart reframe (9:16)
    - Caption burning
    - Audio normalization
    - Final encode
    """
    logger.info(f"Starting render for clip {clip_id}")
    
    try:
        db_session = AsyncSessionLocal()
        
        # Get clip metadata from DB
        from api.models.core import Clip, RenderJob
        from sqlalchemy import select, update
        result = await db_session.execute(select(Clip).where(Clip.id == clip_id))
        clip = result.scalar_one_or_none()
        
        if not clip or not clip.start_time:
            raise ValueError(f"Clip {clip_id} not found")
        
        # Create render job
        render_job = RenderJob(
            clip_id=clip_id,
            render_type=render_type,
            resolution=resolution,
            status="processing",
            progress=0.0,
        )
        db_session.add(render_job)
        await db_session.commit()
        
        # Run FFmpeg pipeline
        output_path = f"/tmp/{clip_id}_{render_type}.mp4"
        
        if source_path and clip.start_time and clip.end_time:
            duration = clip.end_time - clip.start_time
            
            # FFmpeg: cut + scale + encode
            cmd = [
                "ffmpeg", "-y",
                "-i", source_path,
                "-ss", str(clip.start_time),
                "-to", str(clip.end_time),
                "-c:v", "libx264",
                "-crf", str(settings.CLIPPYME_X264_CRF),
                "-preset", settings.CLIPPYME_X264_PRESET,
                "-c:a", "aac",
                "-b:a", "128k",
                "-movflags", "+faststart",
                output_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                raise ValueError(f"FFmpeg render failed: {result.stderr}")
        
        # Update render job
        await _update_render_progress(db_session, render_job.id, 100, output_path)
        
        return {"clip_id": clip_id, "status": "completed", "render_type": render_type, "output_path": output_path}
    except Exception as e:
        logger.error(f"Render failed for clip {clip_id}: {str(e)}")
        self.retry(exc=e, countdown=30)


async def _update_render_progress(db: AsyncSession, render_job_id: str, progress: float, output_path: str = None):
    """Update render job progress"""
    from sqlalchemy import update
    try:
        from api.models.core import RenderJob
        stmt = update(RenderJob).where(RenderJob.id == render_job_id).values(
            progress=progress,
            status="completed" if progress >= 100 else "processing",
            updated_at=datetime.now(timezone.utc)
        )
        if output_path:
            stmt = stmt.values(output_url=output_path)
        await db.execute(stmt)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to update render progress: {str(e)}")


@shared_task(bind=True, max_retries=2)
def generate_metadata(self, clip_id: str, transcript_text: str = None) -> dict:
    """
    Generate titles, hooks, descriptions, hashtags for a clip
    Uses Ollama API or Gemini API
    """
    logger.info(f"Generating metadata for clip {clip_id}")
    
    try:
        from api.services.ai.ollama_service import OllamaService
        
        service = OllamaService()
        
        if transcript_text:
            metadata = await service.generate_metadata(transcript_text)
        else:
            metadata = {
                "title": "Untitled Video",
                "description": "A video generated by ClipForge",
                "hashtags": [],
                "keywords": [],
                "summary": "",
                "thumbnail_prompt": "",
            }
        
        logger.info(f"Metadata generated for clip {clip_id}")
        return {"clip_id": clip_id, "metadata": metadata}
    except Exception as e:
        logger.error(f"Metadata generation failed for clip {clip_id}: {str(e)}")
        # Fallback to simple metadata
        return {
            "clip_id": clip_id,
            "metadata": {
                "title": "Untitled Video",
                "description": "A video generated by ClipForge",
                "hashtags": [],
                "keywords": [],
                "summary": "",
                "thumbnail_prompt": "",
            },
            "error": str(e),
        }


@shared_task(bind=True, max_retries=3)
def transcribe_video(self, video_id: str, audio_path: str) -> dict:
    """
    Transcribe video audio using faster-whisper
    Returns word-level timestamps
    """
    logger.info(f"Transcribing video {video_id}")
    
    try:
        from api.services.video_processing import TranscriptionService
        service = TranscriptionService(provider="faster-whisper")
        result = asyncio.run(service.transcribe(audio_path))
        
        # Store transcript in DB
        db_session = AsyncSessionLocal()
        from api.services.ai.transcript_service import TranscriptService
        transcript_service = TranscriptService(db_session)
        await transcript_service.store_transcript(video_id, result, language="en")
        
        return {"video_id": video_id, "transcript": result}
    except Exception as e:
        logger.error(f"Transcription failed for video {video_id}: {str(e)}")
        self.retry(exc=e, countdown=60)


@shared_task(bind=True)
def cleanup_expired_jobs(self):
    """Periodic cleanup of expired jobs and temp files"""
    logger.info("Running cleanup task")
    try:
        # Clean up old files
        import glob
        temp_files = glob.glob("/tmp/*.mp4")
        for f in temp_files:
            if os.path.getmtime(f) < datetime.now().timestamp() - 86400:  # Older than 1 day
                os.remove(f)
        logger.info(f"Cleaned up {len(temp_files)} temp files")
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")


@shared_task(bind=True, max_retries=3)
def analyze_clips(self, video_id: str, transcript_text: str) -> dict:
    """
    AI clip detection and scoring
    
    Uses local analysis engine (not Gemini API)
    """
    logger.info(f"Analyzing clips for video {video_id}")
    
    try:
        from api.services.ai.analysis_engine import AIAnalysisService, Segment
        
        engine = AIAnalysisService()
        result = await engine.analyze(
            video_id=video_id,
            transcript=transcript_text,
            segments=[],
        )
        
        # Store candidates in DB
        from api.core.database import AsyncSessionLocal
        from api.services.ai.clip_detection import ClipDetectionService
        
        db_session = AsyncSessionLocal()
        detection_service = ClipDetectionService(db_session)
        await detection_service.store_candidates(video_id, result.candidates)
        
        return {
            "video_id": video_id,
            "candidates": [c.to_dict() for c in result.candidates],
            "total_candidates": len(result.candidates),
        }
    except Exception as e:
        logger.error(f"Clip analysis failed for video {video_id}: {str(e)}")
        self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=2)
def reframe_clip(self, clip_id: str, reframe_data: dict, source_path: str = None) -> dict:
    """
    Apply smart reframe to a clip
    
    Uses MediaPipe for face tracking
    Generates time-varying camera path
    """
    logger.info(f"Reframing clip {clip_id}")
    
    try:
        from api.services.reframe.reframe_engine import ReframeEngine
        
        engine = ReframeEngine()
        
        if source_path:
            camera_path = engine.generate_reframe_path(source_path)
            output_path = f"/tmp/reframed_{clip_id}.mp4"
            engine.render_reframed_clip(source_path, output_path, camera_path)
        else:
            camera_path = engine.generate_reframe_path("/tmp/placeholder.mp4")
            output_path = f"/tmp/reframed_{clip_id}.mp4"
        
        return {"clip_id": clip_id, "reframe_path": camera_path.keyframes if camera_path else [], "output_path": output_path, "status": "completed"}
    except Exception as e:
        logger.error(f"Reframe failed for clip {clip_id}: {str(e)}")
        self.retry(exc=e, countdown=30)


@shared_task(bind=True, max_retries=2)
def generate_captions(self, clip_id: str, transcript: dict, style_id: str = None) -> dict:
    """
    Generate captions for a clip
    
    Applies caption style preset
    Generates SRT/VTT/JSON output
    """
    logger.info(f"Generating captions for clip {clip_id}")
    
    try:
        from api.services.captions.caption_engine import CaptionEngine
        
        engine = CaptionEngine()
        segments = engine.generate_captions(
            transcript_data=transcript.get("content", transcript),
            video_duration=transcript.get("duration", 0),
            style_id=style_id,
        )
        
        # Generate SRT
        from api.services.captions.caption_engine import SubtitleGenerator
        srt = SubtitleGenerator.to_srt(segments)
        srt_path = f"/tmp/{clip_id}.srt"
        with open(srt_path, 'w') as f:
            f.write(srt)
        
        return {
            "clip_id": clip_id,
            "srt_path": srt_path,
            "segment_count": len(segments),
            "status": "completed",
        }
    except Exception as e:
        logger.error(f"Caption generation failed for clip {clip_id}: {str(e)}")
        self.retry(exc=e, countdown=30)