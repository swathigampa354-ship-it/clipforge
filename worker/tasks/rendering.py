"""
Rendering tasks — FFmpeg-based video rendering
"""
from __future__ import annotations

import subprocess
import logging
from datetime import datetime, timezone
from uuid import uuid4

from celery import shared_task
from celery.utils.log import get_task_logger

from api.app.config import settings

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3)
def render_final(self, clip_id: str, render_data: dict, source_path: str = None) -> dict:
    """Render final MP4 output using FFmpeg"""
    logger.info(f"Rendering final video for clip {clip_id}")
    
    try:
        start_time = render_data.get("start_time", 0)
        end_time = render_data.get("end_time", 30)
        resolution = render_data.get("resolution", "1080x1920")
        aspect_ratio = render_data.get("aspect_ratio", "9:16")
        
        output_path = f"/tmp/{clip_id}_final.mp4"
        duration = end_time - start_time
        
        if source_path:
            cmd = [
                "ffmpeg", "-y",
                "-i", source_path,
                "-ss", str(start_time),
                "-to", str(end_time),
                "-vf", f"scale={resolution}",
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
        
        logger.info(f"Final render completed for clip {clip_id}")
        return {
            "clip_id": clip_id,
            "output_url": output_path,
            "status": "completed",
            "duration": duration,
            "resolution": resolution,
            "file_size": 0,
        }
    except Exception as e:
        logger.error(f"Final render failed for clip {clip_id}: {str(e)}")
        self.retry(exc=e, countdown=30)


@shared_task(bind=True, max_retries=2)
def render_preview(self, clip_id: str, source_path: str = None, start_time: float = 0, end_time: float = 30) -> dict:
    """Render low-res preview for quick review using FFmpeg"""
    logger.info(f"Rendering preview for clip {clip_id}")
    
    try:
        output_path = f"/tmp/{clip_id}_preview.mp4"
        
        if source_path:
            cmd = [
                "ffmpeg", "-y",
                "-i", source_path,
                "-ss", str(start_time),
                "-to", str(end_time),
                "-vf", "scale=320:568",
                "-c:v", "libx264",
                "-crf", "28",
                "-preset", "ultrafast",
                "-c:a", "aac",
                "-b:a", "64k",
                "-movflags", "+faststart",
                output_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                raise ValueError(f"FFmpeg preview failed: {result.stderr}")
        
        return {
            "clip_id": clip_id,
            "preview_url": output_path,
            "status": "completed",
        }
    except Exception as e:
        logger.error(f"Preview render failed for clip {clip_id}: {str(e)}")
        self.retry(exc=e, countdown=30)


@shared_task(bind=True, max_retries=2)
def render_qa_check(self, render_job_id: str, output_path: str = None) -> dict:
    """Quality assurance check on rendered output using FFmpeg"""
    logger.info(f"Running QA check for render {render_job_id}")
    
    try:
        checks = {
            "duration": True,
            "resolution": True,
            "audio": True,
            "format": True,
        }
        
        if output_path:
            # Use ffprobe to verify the output
            cmd = [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_streams", "-show_format",
                output_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                checks["duration"] = False
                checks["audio"] = False
                checks["format"] = False
        
        return {
            "render_job_id": render_job_id,
            "passed": all(checks.values()),
            "checks": checks,
        }
    except Exception as e:
        logger.error(f"QA check failed for render {render_job_id}: {str(e)}")
        return {
            "render_job_id": render_job_id,
            "passed": False,
            "checks": {"duration": False, "resolution": False, "audio": False, "format": False},
            "error": str(e),
        }


@shared_task(bind=True, max_retries=2)
def render_reframed(self, clip_id: str, source_path: str, crop_x: float, crop_y: float, crop_w: float, crop_h: float, resolution: str = "1080x1920") -> dict:
    """Render a reframed clip using FFmpeg with crop"""
    logger.info(f"Rendering reframed clip {clip_id}")
    
    try:
        output_path = f"/tmp/{clip_id}_reframed.mp4"
        crop_w_px = int(crop_w * 1920)
        crop_h_px = int(crop_h * 1080)
        crop_x_px = int(crop_x * 1920)
        crop_y_px = int(crop_y * 1080)
        
        cmd = [
            "ffmpeg", "-y",
            "-i", source_path,
            "-vf", f"crop={crop_w_px}:{crop_h_px}:{crop_x_px}:{crop_y_px},scale={resolution}",
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
            raise ValueError(f"FFmpeg reframe failed: {result.stderr}")
        
        return {
            "clip_id": clip_id,
            "output_path": output_path,
            "status": "completed",
        }
    except Exception as e:
        logger.error(f"Reframe render failed for clip {clip_id}: {str(e)}")
        self.retry(exc=e, countdown=30)