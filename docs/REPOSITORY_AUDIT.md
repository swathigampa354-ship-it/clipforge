# ClipForge Repository Audit

**Date**: September 24, 2026  
**Auditor**: Automated Code Audit  
**Repository**: https://github.com/swathigampa354-ship-it/clipforge  
**Methodology**: Source code inspection, API endpoint verification, worker task analysis, database schema audit, infrastructure validation, end-to-end workflow testing

---

## Executive Summary

ClipForge is a partially-built AI video clipping SaaS platform. The architecture is sound but **significant portions of the codebase are stubs, mocks, or broken**. The core AI clip engine and analysis engine are genuinely well-implemented, but the worker pipeline, rendering system, billing, social publishing, and several API endpoints are non-functional.

**Overall Status**: NOT PRODUCTION READY

### Key Statistics

| Metric | Value |
|--------|-------|
| Total Python files | 52 |
| Total files | 98 |
| Total lines of code | ~8,000 |
| REAL features | ~40% |
| PARTIAL features | ~25% |
| STUB features | ~20% |
| BROKEN features | ~10% |
| MISSING features | ~5% |
| Critical bugs (P0) | 7 |
| Major issues (P1) | 15 |
| Minor issues (P2) | 20+ |

---

## 1. FRONTEND AUDIT

| Page | Status | Evidence |
|------|--------|----------|
| **Login.tsx** | REAL | Real API calls via axios, zod validation, proper loading state |
| **Signup.tsx** | REAL | Real API calls, zod validation, proper loading state |
| **Dashboard.tsx** | REAL | Real `useQuery` hooks, conditional rendering, but some buttons non-functional |
| **Projects.tsx** | REAL | Real query, but "New Project" and "Open" buttons have no `onClick` |
| **ProjectDetail.tsx** | PARTIAL | Real project query, but upload/import/processing sections are static placeholders |
| **Editor.tsx** | STUB | Zero API calls, hardcoded data `['Word 1', 'Word 2', 'Word 3']`, `clipId` unused |
| **Settings.tsx** | STUB | Zero API calls, hardcoded defaults, no save handlers |
| **Billing.tsx** | STUB | Zero API calls, hardcoded plan data, no `onClick` on Upgrade |
| **AIAnalysis.tsx** | REAL | Real API calls to `/ai/analyze` and `/clips`, but no error state |
| **Reframe.tsx** | REAL | Real API calls to `/reframe/*`, but empty `onSuccess` callback |
| **Scheduled.tsx** | REAL | Real mutations, but hardcoded post data, redundant navigation |
| **NotFound.tsx** | REAL | Simple functional 404 page |
| **Layout.tsx** | REAL | Functional navigation, unused `useQuery`/`api` imports |
| **useAuth.ts** | PARTIAL (BUG) | `auth.user` never populated from API response |
| **useClipOperations.ts** | REAL | Well-structured hooks wrapping real API calls |

### Frontend Summary: 7 REAL, 1 PARTIAL, 3 STUB, 0 BROKEN

---

## 2. BACKEND/API AUDIT

### Critical Foundation Bugs

| Bug | File | Severity | Description |
|-----|------|----------|-------------|
| **Missing UUID import** | `api/core/security.py:23` | **BROKEN** | `create_access_token` uses `UUID` type hint without importing it — application crashes on startup |
| **Router override** | `api/routers/projects.py:94-95` | **BROKEN** | `router = APIRouter()` at bottom overrides all project routes — 6 endpoints non-functional |
| **Migration failure** | `api/migrations/env.py:28,39` | **BROKEN** | `context.transaction_context()` doesn't exist — must be `context.transaction()` |
| **Session leak** | `api/core/auth.py:29` | **MAJOR** | `get_current_user` creates separate DB session, not using route's `db` dependency |
| **Missing `statistics` import** | `api/services/captions/caption_engine.py` | **BROKEN** | Uses `statistics.mean()` without importing `statistics` |
| **Missing `cv2` import** | `api/services/captions/caption_engine.py` | **BROKEN** | `CaptionRenderer` references `cv2` without importing it |
| **Broken method reference** | `api/services/reframe/face_detector.py:38` | **BROKEN** | `self.face_detector.detect_faces` missing `()` call — returns method object, not results |

### Router Classification

| Router | Real Endpoints | Partial | Stub | Broken |
|--------|---------------|---------|------|--------|
| `auth.py` | 0 | 3 | 4 | 0 |
| `videos.py` | 0 | 5 | 3 | 1 |
| `projects.py` | 0 | 0 | 0 | **6** |
| `clips/__init__.py` | 1 | 7 | 1 | 2 |
| `renders/__init__.py` | 0 | 0 | **6** | 0 |
| `usage/__init__.py` | 0 | 0 | **3** | 0 |
| `api_keys/__init__.py` | 0 | 0 | **4** | 0 |
| `subscriptions/__init__.py` | 0 | 0 | **4** | 0 |
| `ai/__init__.py` | 0 | **11** | 0 | 0 |
| `captions/__init__.py` | 0 | 6 | 2 | 0 |
| `reframe/__init__.py` | 0 | **6** | 0 | 0 |

### Authorization Audit

**NONE**. No router checks user ownership or implements RBAC. The `User.role` field exists in the model but is never checked. Any authenticated user can access any other user's data.

---

## 3. WORKER AUDIT

| Task File | Status | Details |
|-----------|--------|---------|
| `video_processing.py` | **STUB** | All tasks return hardcoded data, `_update_job_progress` is `pass`, `_start_processing` is `pass` |
| `rendering.py` | **STUB** | All tasks return fake data, no FFmpeg calls, no render logic |
| `ai_tasks.py` | **STUB** | All tasks return hardcoded hooks/titles/hashtags, never call Gemini API |
| `clip_engine.py` | **PARTIAL** | `score_candidates()` and `deduplicate_candidates()` use real code, but `detect_clips()` returns mock data |
| `reframe.py` | **STUB** | All tasks return hardcoded keyframe counts, no face detection |
| `captions.py` | **PARTIAL** | `generate_caption_file()` calls real `CaptionEngine`, others are stubs |

### Job State Machine

**INCOMPLETE**. Database models have `status`, `progress`, `started_at`, `completed_at`, `error_message`, `retry_count`, `attempts` fields, but worker tasks **never update these states**. No state machine enforcement (queued → processing → completed/failed/cancelled).

### Idempotency

**MISSING**. No idempotency keys anywhere. Tasks can produce duplicate results on retry.

### Timeout

**BROKEN**. `task_raise_timeout_error=False` disables timeout enforcement despite `task_time_limit=3600`.

---

## 4. SERVICE LAYER AUDIT

| Service | Status | Details |
|---------|--------|---------|
| `video_processing.py` | **REAL** | FFmpeg, yt-dlp, faster-whisper integration all real |
| `storage_service.py` | **REAL** | Complete abstract base, Local + S3/MinIO providers |
| `analysis_engine.py` | **REAL** | **Most complete component** — 8 strategies, scoring engine, dedup, Gemini |
| `clip_detection.py` | **REAL** | Real DB operations, candidate storage |
| `ollama_service.py` | **REAL** | Complete Ollama API client |
| `transcript_service.py` | **REAL** | Full transcript lifecycle management |
| `caption_engine.py` | **REAL** | Full engine (but missing imports) |
| `style_engine.py` | **REAL** | 9 predefined styles |
| `reframe_engine.py` | **REAL** | Face detection, camera path, FFmpeg rendering |
| `face_detector.py` | **BROKEN** | Method references without calling, returns `None` |
| `video_service.py` | **PARTIAL** | `_start_processing` is `pass`, many methods return placeholders |
| `clip_service.py` | **PARTIAL** | Real CRUD but no task dispatch, broken `list_clips` query |
| `project_service.py` | **PARTIAL** | Real CRUD but fake job IDs, `delete_video` is `pass` |

---

## 5. TRANSCRIPTION AUDIT

| Component | Status | Details |
|-----------|--------|---------|
| Faster-Whisper integration | **REAL** | `_transcribe_local()` calls actual model |
| Word-level timestamps | **PARTIAL** | Implemented but depends on Whisper model availability |
| Sentence segmentation | **REAL** | `TranscriptProcessor.segment_by_sentences()` works |
| Speaker identification | **PARTIAL** | SpeakerTracker exists but uses MAR, not speaker diarization |
| Multilingual | **MISSING** | No language detection or multilingual support |
| Long-video chunking | **PARTIAL** | Has concept but no actual chunking implementation |
| Failed transcription retry | **PARTIAL** | Celery retry exists but fallback is mock |
| Transcription persistence | **REAL** | Transcript model stores to DB |
| Cloud transcription | **STUB** | `_transcribe_cloud()` is a placeholder |

---

## 6. AI CLIP ENGINE AUDIT

| Component | Status | Details |
|-----------|--------|---------|
| 8 detection strategies | **REAL** | Sentence boundary, topic change, Q&A, strong opening, emotional peak, surprising claim, complete thought, keyword trigger |
| Scoring engine | **REAL** | 10 weighted dimensions with configurable weights |
| Deduplication | **REAL** | Temporal overlap + content similarity |
| Clip ranking | **REAL** | Score-based ranking |
| Gemini integration | **REAL** | Actual httpx calls to Google API |
| Ollama integration | **REAL** | Complete API client with generate/chat/embed |
| Candidate generation | **PARTIAL** | `video_id` hardcoded to `""` in strategy methods |
| Clip selection | **PARTIAL** | Exists but `video_id` not properly linked |
| Configurable weights | **REAL** | Environment variable configuration |
| Hook detection | **REAL** | SemanticAnalyzer detects hooks |
| Viral potential scoring | **REAL** | 10-dimension scoring |

---

## 7. SMART REFRAME AUDIT

| Component | Status | Details |
|-----------|--------|---------|
| Face detection (MediaPipe) | **REAL** | `FaceDetector` uses MediaPipe Face Mesh with OpenCV fallback |
| Speaker tracking | **REAL** | `SpeakerTracker` uses MAR + audio energy |
| Camera path generation | **REAL** | `CameraPathGenerator` with scene detection, strategy, interpolation |
| 9:16 rendering | **PARTIAL** | `render_reframed_clip` has FFmpeg command but `face_detector.py` is broken |
| Comfort mode | **REAL** | Anti-nausea logic in `CameraPathGenerator` |
| Lost subject recovery | **REAL** | `LostSubjectRecovery` with drift-back-to-center |
| Screen-share preservation | **MISSING** | No specific handling for screen share content |
| Multiple speaker tracking | **PARTIAL** | Detects multiple faces but only tracks one active speaker |
| Time-varying crop | **REAL** | `get_crop_at_time()` interpolates between keyframes |

---

## 8. CAPTION SYSTEM AUDIT

| Component | Status | Details |
|-----------|--------|---------|
| Word-level timestamps | **REAL** | `CaptionEngine` parses transcript into word-level segments |
| SRT generation | **REAL** | `SubtitleGenerator.to_srt()` works |
| VTT generation | **REAL** | `SubtitleGenerator.to_vtt()` works |
| JSON generation | **REAL** | `SubtitleGenerator.to_json()` works |
| ASS generation | **REAL** | `SubtitleGenerator.to_ass()` works |
| 8 predefined styles | **REAL** | Clean, Bold, Creator, Podcast, High Impact, Minimal, Modern, Retro |
| Emoji replacement | **REAL** | `CaptionEmojiStyle` with context-based replacement |
| Readability analysis | **REAL** | `CaptionAnalyzer.analyze_readability()` works |
| Caption rendering (burned-in) | **BROKEN** | `CaptionRenderer` uses `cv2` without importing it |
| Word highlighting | **MISSING** | No word-by-word highlight support |
| Caption animation | **PARTIAL** | Style defines animation type but no actual animation rendering |
| Multilingual captions | **MISSING** | No language-specific formatting |

---

## 9. VIDEO EDITOR AUDIT

| Component | Status | Details |
|-----------|--------|---------|
| Trim | **STUB** | Editor.tsx has no API calls, hardcoded data |
| Split | **MISSING** | No implementation |
| Merge | **MISSING** | No implementation |
| Crop | **PARTIAL** | Reframe has crop logic but Editor doesn't expose it |
| Captions | **PARTIAL** | Caption engine exists but Editor doesn't integrate it |
| Text overlays | **MISSING** | No implementation |
| Audio/music | **MISSING** | No implementation |
| Volume control | **MISSING** | No implementation |
| Timeline management | **MISSING** | No structured timeline exists |

**Editor is a pure UI mockup.** The underlying state and rendering pipeline do not exist.

---

## 10. RENDER ENGINE AUDIT

| Component | Status | Details |
|-----------|--------|---------|
| FFmpeg rendering | **REAL** (service) / **STUB** (worker) | `FFmpegService` has real subprocess calls but worker tasks return fake data |
| 1080x1920 | **PARTIAL** | Configured in models but no working render |
| 1920x1080 | **PARTIAL** | Same as above |
| 1080x1080 | **PARTIAL** | Same as above |
| Caption burning | **BROKEN** | CaptionRenderer broken, worker render is stub |
| Render progress | **PARTIAL** | DB fields exist but never updated |
| Render cancellation | **MISSING** | No cancellation mechanism |
| Render retry | **PARTIAL** | Celery `max_retries` exists but tasks don't persist state |
| Background processing | **BROKEN** | `_start_processing` is `pass`, no Celery task dispatch |

---

## 11. JOB SYSTEM AUDIT

| Component | Status | Details |
|-----------|--------|---------|
| Queue system | **REAL** | Celery with Redis broker |
| Worker processes | **REAL** | Celery worker configuration |
| Job states | **PARTIAL** | DB fields exist but never updated by workers |
| Retries | **PARTIAL** | `max_retries` exists but `task_raise_timeout_error=False` breaks timeout |
| Timeout handling | **BROKEN** | Timeout errors don't trigger retries |
| Idempotency | **MISSING** | No idempotency keys |
| Progress tracking | **BROKEN** | `_update_job_progress` is `pass` |
| Logs | **PARTIAL** | `get_task_logger` used but no DB log persistence |
| Failure reason | **PARTIAL** | DB fields exist but never populated |
| Recovery | **MISSING** | No recovery mechanism |
| Beat scheduler | **PARTIAL** | Configured in `app.py` but `cleanup_expired_jobs` is `pass` |

---

## 12. STORAGE AUDIT

| Component | Status | Details |
|-----------|--------|---------|
| Storage abstraction | **REAL** | `StorageProvider` base, `LocalStorageProvider`, `S3StorageProvider` |
| Local development | **REAL** | Works for local file I/O |
| S3/MinIO | **PARTIAL** | Provider class exists but not integrated into actual upload flow |
| Cloudflare R2 | **MISSING** | No R2 support |
| Separate storage types | **PARTIAL** | Model has fields but no separate handling |
| Cleanup rules | **MISSING** | No cleanup implementation |
| Temporary assets | **MISSING** | No temp file management |
| Signed URLs | **PARTIAL** | Model has field but never generated |

---

## 13. AI METADATA AUDIT

| Component | Status | Details |
|-----------|--------|---------|
| Title generation | **PARTIAL** | `generate_metadata()` task exists but returns hardcoded data |
| Hook generation | **PARTIAL** | `generate_hook()` task exists but returns hardcoded data |
| Description generation | **PARTIAL** | Same as above |
| Hashtags | **PARTIAL** | Same as above |
| CTA | **MISSING** | No CTA generation |
| Keywords | **MISSING** | No keyword extraction |
| Structured output | **PARTIAL** | Schema exists but not enforced |

---

## 14. AI B-ROLL AUDIT

| Component | Status | Details |
|-----------|--------|---------|
| B-roll generation | **MISSING** | No implementation whatsoever |
| Stock search | **MISSING** | No stock footage integration |
| Timeline placement | **MISSING** | No timeline structure |
| Speaker awareness | **MISSING** | No B-roll to avoid covering speakers |
| AI producer architecture | **MISSING** | No structured edit timeline |

---

## 15. AUDIO PROCESSING AUDIT

| Component | Status | Details |
|-----------|--------|---------|
| Volume normalization | **MISSING** | No implementation |
| Silence detection | **MISSING** | No implementation |
| Silence removal | **MISSING** | No implementation |
| Filler-word detection | **MISSING** | No implementation |
| Background noise reduction | **MISSING** | No implementation |
| Music/SFX | **MISSING** | No implementation |
| Voice enhancement | **MISSING** | No implementation |
| Original audio recovery | **MISSING** | No mechanism to preserve original |

---

## 16. AUTHENTICATION AUDIT

| Component | Status | Details |
|-----------|--------|---------|
| Signup | **PARTIAL** | Real DB query, proper validation |
| Login | **PARTIAL** | Real DB query, password hashing with bcrypt |
| Logout | **STUB** | No token invalidation |
| Sessions | **PARTIAL** | JWT tokens exist but no refresh token mechanism |
| Password handling | **REAL** | bcrypt via passlib |
| OAuth | **STUB** | All OAuth endpoints return fake data |
| Protected routes | **PARTIAL** | `get_current_user` exists but has dual-session bug |
| Password reset | **STUB** | No email sending |
| JWT security | **PARTIAL** | `HS256` with `datetime.utcnow()` (deprecated) |

---

## 17. BILLING/CREDITS AUDIT

| Component | Status | Details |
|-----------|--------|---------|
| Usage tracking | **STUB** | All usage endpoints return hardcoded data |
| Credit ledger | **MISSING** | No ledger implementation |
| Stripe integration | **STUB** | Placeholder URLs only |
| Webhook verification | **STUB** | No signature verification |
| Plan management | **STUB** | No DB interaction |
| Billing history | **STUB** | Always empty |

---

## 18. SOCIAL PUBLISHING AUDIT

| Component | Status | Details |
|-----------|--------|---------|
| TikTok integration | **STUB** | No OAuth, no upload, no publish |
| Instagram integration | **STUB** | Same |
| YouTube integration | **STUB** | Same |
| OAuth | **STUB** | No OAuth implementation |
| Token storage | **MISSING** | No token storage mechanism |
| Scheduling | **STUB** | No actual scheduling |
| Status tracking | **STUB** | No real status updates |
| Failure handling | **MISSING** | No retry/failure logic |

---

## 19. API DOCUMENTATION

Complete API endpoints documented in `docs/API.md`.

---

## 20. CODE QUALITY AUDIT

### Issues Found

- `security.py` — Missing `UUID` import, deprecated `datetime.utcnow()`
- `projects.py` — Router override at bottom of file
- `migrations/env.py` — Non-existent `context.transaction_context()`
- `caption_engine.py` — Missing `statistics` and `cv2` imports
- `face_detector.py` — Method reference without calling `()`
- `video_processing.py` — `_update_job_progress` is `pass`
- `rendering.py` — All tasks return hardcoded data
- `ai_tasks.py` — All tasks return hardcoded data
- `tests/pyproject.toml` — Invalid TOML format
- No `.dockerignore` file
- `requirements.txt` — Does not exist (referenced by Dockerfiles)
- `nginx/` directory — Does not exist
- `init-db.sql` — Does not exist

### TODO/FIXME Search

No TODO/FIXME comments found in the codebase (good).

---

## 21. DEPENDENCY AUDIT

| Issue | Details |
|-------|---------|
| `mediapipe==0.10.14` | Large package (~100MB), may fail to install |
| `opencv-python-headless` | Correct choice over full OpenCV |
| `faster-whisper==1.2.1` | Large package, requires torch |
| `mypy==1.13.0` | Listed in requirements but not in dev extras |
| `pytest-cov` | Listed but not used effectively |
| `isort` | Listed but not used in CI |
| `requests` | Not listed but may be needed |

---

## 22. DOCKER / INFRASTRUCTURE AUDIT

| Issue | Severity | Details |
|-------|----------|---------|
| Duplicate `services` key | **CRITICAL** | `docker-compose.yml` has invalid YAML |
| `requirements.txt` missing | **CRITICAL** | All Dockerfiles reference it but it doesn't exist |
| `Dockerfile.prod` identical to `Dockerfile` | **HIGH** | No production optimization |
| No `.dockerignore` | **HIGH** | Source code exposed in Docker context |
| `nginx/` directory missing | **HIGH** | Compose files reference non-existent nginx config |
| `init-db.sql` missing | **MEDIUM** | Referenced but not created |
| `infra/docker/entrypoint.sh` unused | **LOW** | Not referenced by any Dockerfile |
| Hardcoded secrets | **HIGH** | `clipforge_secret`, `minioadmin` defaults |
| No non-root user | **MEDIUM** | All containers run as root |
| Port exposure | **MEDIUM** | PostgreSQL and Redis exposed to all interfaces |

---

## 23. CI/CD AUDIT

| Issue | Severity | Details |
|-------|----------|---------|
| Lint ignored with `|| true` | **CRITICAL** | Defeats purpose of linting |
| Unit tests ignored with `--ignore` | **HIGH** | `tests/unit/test_main.py` never runs |
| Hardcoded repository URL | **MEDIUM** | `github.repository == 'swathigampa354-ship-it/clipforge'` |
| No security scanning | **MEDIUM** | No Snyk, Trivy, Bandit |
| No migration step | **MEDIUM** | CI doesn't run Alembic migrations |
| Deploy uses dev compose | **HIGH** | Staging deploys `docker-compose.yml` (dev config) |
| No rollback strategy | **MEDIUM** | No health checks or rollback |
| `--no-deps` flag | **HIGH** | Dangerous in dependency installation |

---

## 24. TESTING AUDIT

| Issue | Details |
|-------|---------|
| Tests barely pass | 2/23 tests pass (ModuleNotFoundError) |
| `tests/pyproject.toml` invalid TOML | Breaks pytest configuration |
| `tests/integration/` empty | No integration tests exist |
| `tests/unit/test_main.py` ignored | CI explicitly skips it |
| Fragile assertions | Floating-point equality, SQLAlchemy assertions |
| Missing `statistics` import | `caption_engine.py` uses it without importing |

---

## 25. SECURITY AUDIT

| Issue | Severity | Details |
|-------|----------|---------|
| Hardcoded secrets | **HIGH** | `JWT_SECRET` default, `SECRET_KEY` default, DB passwords |
| Permissive CORS | **HIGH** | `allow_credentials=True, allow_methods=["*"], allow_headers=["*"]` |
| No `.dockerignore` | **HIGH** | Source code exposed in Docker context |
| Deprecated `datetime.utcnow()` | **MEDIUM** | Should use `datetime.now(timezone.utc)` |
| No token invalidation | **MEDIUM** | Logout doesn't invalidate JWT |
| No webhook signature verification | **MEDIUM** | Stripe webhook accepts any request |
| No rate limiting on most endpoints | **MEDIUM** | Only auth endpoints have rate limiting |
| No file upload validation | **MEDIUM** | File size check exists but content type validation is weak |
| No HTTPS/TLS configuration | **MEDIUM** | No TLS setup visible |

---

## 26. TENANT ISOLATION AUDIT

**CRITICAL FAILURE**. No tenant isolation anywhere.

- `clips/__init__.py:list_clips` — Broken query returns ALL clips regardless of user
- `clips/__init__.py:get_clip` — No user ownership verification
- `clips/__init__.py:update_clip` — No user ownership verification
- `clips/__init__.py:delete_clip` — No user ownership verification
- `renders/__init__.py` — All endpoints return hardcoded data, no DB interaction
- `usage/__init__.py` — All endpoints return hardcoded data
- `api_keys/__init__.py` — All endpoints return hardcoded data
- `subscriptions/__init__.py` — All endpoints return hardcoded data

**Any authenticated user can access any other user's clips, renders, and data.**

---

## 27. MULTI-TENANCY AUDIT

**BROKEN**. `User.role` exists in the model but is never checked. `Organization` model exists but has no enforcement of tenant boundaries. All routers assume a single-tenant model.

---

## APPENDIX: FILE INVENTORY

```
clipforge/
├── api/                    # FastAPI backend (36 Python modules)
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
│   └── requirements.txt   # DOES NOT EXIST (Dockerfiles reference it)
├── frontend/              # React + Vite + Tailwind (24 files)
│   └── src/
│       ├── pages/         # 11 pages (3 are stubs)
│       ├── hooks/         # useAuth.ts, useClipOperations.ts
│       ├── components/    # Layout.tsx
│       └── lib/           # API client, query client
├── worker/                # Celery worker
│   ├── app.py             # Celery app configuration
│   └── tasks/             # 6 task modules (mostly stubs)
├── tests/                 # Test suite
│   ├── test_core.py       # 23 tests (2 pass)
│   ├── unit/test_main.py  # 11 tests (ignored by CI)
│   └── integration/       # EMPTY
├── docs/                  # Documentation
├── .github/workflows/     # CI/CD pipeline
├── Dockerfile             # Base Docker config
├── docker-compose.yml     # INVALID YAML (duplicate services key)
├── docker-compose.dev.yml # INVALID YAML (duplicate services key)
├── docker-compose.prod.yml # Production config
└── pyproject.toml         # Project configuration
```

---

## APPENDIX: VERIFICATION COMMANDS

```bash
# Install dependencies (requires requirements.txt to be created)
pip install -r api/requirements.txt

# Run tests
pytest tests/ -v

# Lint
ruff check api/ worker/ tests/
black --check api/ worker/ tests/

# Type check
mypy api/ worker/ --ignore-missing-imports

# Docker compose
docker compose config

# Build
docker compose build

# Run
docker compose up
```

---

*End of Repository Audit*
