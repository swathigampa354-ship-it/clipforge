# ClipForge Architecture

## Overview

ClipForge is a modular monolith with a Celery worker architecture for AI video processing.

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Frontend   │────▶│    API       │────▶│   PostgreSQL    │
│   React      │     │   FastAPI    │     │   (PostgreSQL)  │
│   (Vite)     │◀────│              │◀────│                 │
└─────────────┘     └──────┬───────┘     └─────────────────┘
                          │
                          │ Celery Tasks
                          ▼
                   ┌──────────────┐     ┌─────────────────┐
                   │   Worker     │────▶│     Redis        │
                   │   (Celery)   │     │   (Broker/Cache) │
                   └──────┬───────┘     └─────────────────┘
                          │
                          │ FFmpeg / MediaPipe / Whisper
                          ▼
                   ┌──────────────┐
                   │   Object     │
                   │   Storage    │
                   │   (MinIO/S3) │
                   └──────────────┘
```

## Layers

### 1. Presentation Layer (Frontend)
- **Framework**: React 18 + Vite + Tailwind CSS
- **State Management**: React Query (TanStack) + Zustand
- **Routing**: React Router v6
- **Pages**: Dashboard, Projects, Editor, Reframe, AI Analysis, Scheduled

### 2. API Layer (Backend)
- **Framework**: FastAPI 0.115.x
- **Authentication**: JWT (HS256) via `python-jose`
- **Database**: SQLAlchemy 2.0 (async) + PostgreSQL 16
- **Rate Limiting**: slowapi
- **Validation**: Pydantic 2.0
- **Migrations**: Alembic

### 3. Worker Layer
- **Queue**: Celery 5.4 with Redis broker
- **Workers**: Processing, Transcription, Rendering, AI queues
- **Scheduler**: Celery Beat with Redis scheduler
- **Retry**: Exponential backoff with max 3 retries

### 4. AI Layer
- **Clip Detection**: 8 strategies (local computation)
- **Scoring**: 10-dimension weighted scoring engine
- **Transcription**: Faster-Whisper (local) or cloud providers
- **LLM Integration**: Gemini API + Ollama API
- **Face Detection**: MediaPipe Face Mesh + OpenCV Haar fallback

### 5. Storage Layer
- **Abstraction**: `StorageProvider` base class
- **Local**: `LocalStorageProvider` for dev
- **S3/MinIO**: `S3StorageProvider` for production
- **Separate Types**: Original videos, audio, transcripts, renders, thumbnails

### 6. Rendering Layer
- **Engine**: FFmpeg (libx264)
- **Resolutions**: 1080x1920, 1920x1080, 1080x1080
- **Captions**: Burned-in via FFmpeg
- **Smart Reframe**: Time-varying crop via camera path

## Key Modules

### AI Clip Engine
- `api/services/ai/analysis_engine.py` — Scoring, dedup, selection
- `api/services/ai/clip_detection.py` — DB operations, candidate storage
- `api/services/ai/transcript_service.py` — Transcript lifecycle
- `api/services/ai/ollama_service.py` — Ollama API integration

### Smart Reframe
- `api/services/reframe/reframe_engine.py` — Face detection, camera path, rendering
- `api/services/reframe/face_detector.py` — Face detection service

### Caption System
- `api/services/captions/caption_engine.py` — Word-level timing, subtitle formats
- `api/services/captions/style_engine.py` — 9 predefined styles

### Storage
- `api/services/storage_service.py` — Provider abstraction
- `api/services/video_processing.py` — FFmpeg, yt-dlp, Whisper

## Database Schema

18 tables across 3 categories:

**User Management**: `users`, `organizations`, `members`
**Content**: `projects`, `videos`, `transcripts`, `clip_candidates`, `clips`, `caption_styles`, `render_jobs`, `render_outputs`
**Operations**: `ai_jobs`, `usage_records`, `subscriptions`, `api_keys`, `scheduled_posts`

## API Routes

All routes under `/api/v1` prefix:
- `/auth/*` — Authentication
- `/projects/*` — Project CRUD
- `/videos/*` — Video upload, import, status
- `/clips/*` — Clip management
- `/reframe/*` — Smart reframe
- `/ai/*` — AI analysis, Ollama
- `/captions/*` — Caption generation
- `/renders/*` — Render management
- `/usage/*` — Usage tracking
- `/api_keys/*` — API key management
- `/subscriptions/*` — Subscription management
- `/scheduled-posts/*` — Social publishing

## Environment Configuration

```
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/clipforge
REDIS_URL=redis://host:6379/0
SECRET_KEY=change-me-in-production
JWT_SECRET=change-me-in-production
CLIPPYME_X264_CRF=23
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

## Deployment

### Development
```bash
docker compose -f docker-compose.dev.yml up
```

### Production
```bash
docker compose -f docker-compose.prod.yml up
```

### GPU Support
```bash
docker compose -f docker-compose.gpu.yml up
```

---

*Last updated: September 24, 2026*