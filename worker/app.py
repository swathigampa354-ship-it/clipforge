# Update worker/app.py to include all tasks
from celery import Celery

from api.app.config import settings

redis_url = settings.REDIS_URL

celery_app = Celery(
    "clipforge",
    broker=redis_url,
    backend=redis_url,
    include=[
        "worker.tasks.video_processing",
        "worker.tasks.rendering",
        "worker.tasks.ai_tasks",
        "worker.tasks.reframe",
        "worker.tasks.captions",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_raise_timeout_error=False,
    task_time_limit=3600,
    task_soft_time_limit=3000,
    result_expires=86400,
    result_backend=redis_url,
    broker_pool_limit=10,
    broker_connection_retry_on_startup=True,
    worker_max_tasks_per_child=50,
    task_routes={
        "worker.tasks.video_processing.process_video": {"queue": "processing"},
        "worker.tasks.video_processing.transcribe_video": {"queue": "transcription"},
        "worker.tasks.video_processing.render_clip": {"queue": "rendering"},
        "worker.tasks.video_processing.analyze_clips": {"queue": "ai"},
        "worker.tasks.video_processing.generate_metadata": {"queue": "ai"},
        "worker.tasks.reframe.generate_camera_path": {"queue": "rendering"},
        "worker.tasks.reframe.render_reframed_clip": {"queue": "rendering"},
        "worker.tasks.reframe.track_speakers": {"queue": "processing"},
        "worker.tasks.reframe.reframe_preview": {"queue": "rendering"},
        "worker.tasks.captions.generate_caption_file": {"queue": "transcription"},
        "worker.tasks.captions.export_caption_file": {"queue": "rendering"},
        "worker.tasks.captions.analyze_caption_quality": {"queue": "ai"},
        "worker.tasks.captions.render_caption_preview": {"queue": "rendering"},
    },
)

celery_app.conf.beat_schedule = {
    "cleanup-expired-jobs": {
        "task": "worker.tasks.video_processing.cleanup_expired_jobs",
        "schedule": 3600.0,
    },
}


@celery_app.worker_ready.connect
def setup_worker(**kwargs):
    pass
