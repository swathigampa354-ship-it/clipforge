from celery import Celery
from celery.utils.log import get_task_logger
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

import os
import sys
sys.path.insert(0, '/app')

from api.app.config import settings
from api.core.database import Base

engine = create_async_engine(settings.DATABASE_URL, poolclass=None, pool_size=5)
AsyncSessionLocal = async_sessionmaker(engine, class_=async_sessionmaker, expire_on_commit=False, autoflush=False)

logger = get_task_logger(__name__)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def run_job_stage(job_id: str, stage: str, task_func):
    """Execute a job stage with proper error handling and state updates"""
    logger.info(f"Starting stage {stage} for job {job_id}")
    try:
        result = await task_func(job_id)
        logger.info(f"Stage {stage} completed for job {job_id}")
        return result
    except Exception as e:
        logger.error(f"Stage {stage} failed for job {job_id}: {str(e)}")
        raise
