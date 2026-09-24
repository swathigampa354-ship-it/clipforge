from dataclasses import dataclass
from typing import Optional

from pydantic_settings import BaseSettings


@dataclass
class Settings(BaseSettings):
    APP_NAME: str = "ClipForge"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str
    REDIS_URL: str
    JWT_SECRET: str
    JWT_EXPIRY_MINUTES: int = 15

    STORAGE_TYPE: str = "local"
    STORAGE_PATH: str = "./data/storage"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "clipforge"
    MINIO_SECRET_KEY: str = "minio-secret"

    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    DEEPGRAM_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""

    MAX_FILE_SIZE_MB: int = 16384
    CLIPPYME_BIND: str = "0.0.0.0"
    CLIPPYME_API_TOKEN: str = ""
    CLIPPYME_X264_CRF: int = 18
    CLIPPYME_X264_PRESET: str = "medium"
    CLIPPYME_JOB_MAX_ATTEMPTS: int = 3
    CLIPPYME_MIN_VIRAL_SCORE: Optional[str] = None
    CLIPPYME_MAX_CLIPS: Optional[str] = None

    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_PER_HOUR: int = 1000
    WORKER_CONCURRENCY: int = 2

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
