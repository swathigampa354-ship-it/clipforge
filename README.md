# ClipForge

**AI Video Clipping SaaS** — Turn long-form videos into short-form content using AI analysis, smart reframing, and automated captioning.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12+-blue)](https://python.org)
[![React 18](https://img.shields.io/badge/React-18+-61DAFB)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496FD)](https://docker.com)

---

## ⚠️ Project Status: DEVELOPMENT — NOT PRODUCTION READY

This project is under active development. The core AI clip engine, scoring engine, and analysis engine are well-implemented, but the worker pipeline, rendering system, authorization, and most API endpoints are **stubs or broken**. See [docs/REPOSITORY_AUDIT.md](docs/REPOSITORY_AUDIT.md) for a complete audit.

| Feature | Status |
|---------|--------|
| AI Clip Engine | ⚠️ PARTIAL |
| Transcription | ⚠️ PARTIAL |
| Smart Reframe | ⚠️ PARTIAL |
| Captions | ⚠️ PARTIAL |
| Editor | ❌ STUB |
| Rendering | ❌ BROKEN |
| Workers | ❌ BROKEN |
| Authorization | ❌ STUB |
| Billing | ❌ STUB |
| Social Publishing | ❌ STUB |

---

## Overview

ClipForge transforms long-form videos into short-form vertical content using:

```
LONG VIDEO → AI ANALYSIS → BEST MOMENTS → SHORT CLIPS → SMART REFRAMING → CAPTIONS → RENDER → EXPORT
```

## Architecture

- **Backend**: Python 3.12, FastAPI, Celery, PostgreSQL 16, Redis
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Worker**: Celery with Redis-backed task queue
- **Storage**: Local (dev) / S3/MinIO (prod)
- **AI**: Gemini API, Ollama API, Faster-Whisper, MediaPipe, OpenCV
- **Rendering**: FFmpeg (libx264)
- **Deployment**: Docker Compose (dev + production)

## Quick Start

### Docker (Recommended)
```bash
git clone https://github.com/swathigampa354-ship-it/clipforge.git
cd clipforge
cp .env.example .env
# Edit .env with your API keys
docker compose -f docker-compose.dev.yml up --build
```

### Local Development
```bash
# Backend
cd api
pip install -r requirements.txt
cp ../.env.example .env
alembic upgrade head
uvicorn api.app.main:app --reload --port 8000

# Worker
cd worker
celery -A worker.app.celery_app worker --loglevel=info

# Frontend
cd ../frontend
npm install
npm run dev
```

### Access
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000
- MinIO Console: http://localhost:9001

## Project Structure

```
clipforge/
├── api/                    # FastAPI backend (52 Python modules)
│   ├── app/               # Application factory, config, middleware
│   ├── core/              # Database, security, auth, rate limiting
│   ├── models/            # SQLAlchemy models (18 tables)
│   ├── routers/           # REST API endpoints (11 routers)
│   ├── schemas/           # Pydantic request/response models
│   ├── services/          # Business logic services
│   │   ├── ai/            # AI analysis, clip detection, Ollama
│   │   ├── captions/      # Caption engine, style engine
│   │   └── reframe/       # Face detection, reframe engine
│   ├── integrations/      # URL import (yt-dlp)
│   ├── migrations/        # Alembic database migrations
│   └── requirements.txt   # Python dependencies
├── frontend/              # React + Vite + Tailwind
│   └── src/
│       ├── pages/         # 11 pages (3 are stubs)
│       ├── hooks/         # useAuth.ts, useClipOperations.ts
│       └── lib/           # API client, query client
├── worker/                # Celery worker
│   ├── app.py             # Celery app configuration
│   └── tasks/             # 6 task modules
├── tests/                 # Test suite (2/23 tests pass)
├── docs/                  # Documentation (5 documents)
├── .github/workflows/     # CI/CD pipeline
├── Dockerfile             # Base Docker config
├── docker-compose*.yml    # Dev + production configs
├── pyproject.toml         # Project configuration
└── .env.example           # Environment template
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/auth/me` | Get current user |
| POST | `/api/v1/auth/refresh` | Refresh token (stub) |

### Projects
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/projects` | Create project |
| GET | `/api/v1/projects` | List projects |
| GET | `/api/v1/projects/:id` | Get project |
| PUT | `/api/v1/projects/:id` | Update project |
| DELETE | `/api/v1/projects/:id` | Delete project |

### Videos
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/videos/upload` | Upload video |
| POST | `/api/v1/videos/import` | Import from URL |
| GET | `/api/v1/videos/:id` | Get video |
| POST | `/api/v1/videos/:id/analyze` | Start processing |
| GET | `/api/v1/videos/:id/status` | Get processing status |

### AI Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ai/analyze` | Run AI analysis |
| GET | `/api/v1/ai/candidates/:video_id` | Get clip candidates |
| POST | `/api/v1/ai/ollama/generate` | Generate with Ollama |
| GET | `/api/v1/ai/ollama/health` | Check Ollama status |

### Captions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/caption-styles` | List caption styles |
| POST | `/api/v1/captions/generate` | Generate captions |
| POST | `/api/v1/captions/:clip_id/apply` | Apply captions |

### Smart Reframe
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/reframe/:video_id/generate` | Generate reframe path |
| GET | `/api/v1/reframe/:video_id/path` | Get camera path |
| POST | `/api/v1/reframe/:clip_id/reframe` | Reframe clip |

---

## AI Capabilities

### Clip Detection (8 Strategies)
- Sentence boundary detection
- Topic change detection
- Q&A sequence detection
- Strong opening detection
- Emotional peak detection
- Surprising claim detection
- Complete thought detection
- Keyword trigger detection

### Scoring (10 Dimensions)
- Hook strength, Information density, Emotional intensity, Novelty, Curiosity, Narrative completeness, Quotability, Audience relevance, Dead air, Context dependency

### AI Providers
- Google Gemini API (configured)
- Ollama API (configured, local)
- Faster-Whisper (local transcription)

## Deployment

### Development
```bash
docker compose -f docker-compose.dev.yml up --build
```

### Production
```bash
docker compose -f docker-compose.prod.yml up -d
```

### GPU Support
```bash
docker compose -f docker-compose.gpu.yml up --build
```

## Documentation

| Document | Content |
|----------|---------|
| [REPOSITORY_AUDIT.md](docs/REPOSITORY_AUDIT.md) | Complete codebase audit with all findings |
| [OPUSCLIP_GAP_MATRIX.md](docs/OPUSCLIP_GAP_MATRIX.md) | Feature-by-feature comparison against OpusClip |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and module descriptions |
| [API.md](docs/API.md) | Complete API endpoint reference |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Deployment guide |
| [FINAL_VERIFICATION.md](docs/FINAL_VERIFICATION.md) | Final verification and test results |

## License

MIT License — see [LICENSE](LICENSE) for details.

**Note**: [Clips Kitty](https://github.com/ColinGPT9/clips-studio) (AGPL-3.0) was studied but NOT incorporated due to license incompatibility.
