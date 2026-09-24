# ClipForge Deployment Guide

## Prerequisites

- Docker 24+
- Docker Compose 2.20+
- Python 3.12+ (for local development)
- Node.js 20+ (for frontend dev)
- FFmpeg (for video processing)

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/swathigampa354-ship-it/clipforge.git
cd clipforge
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Start the development stack
```bash
docker compose -f docker-compose.dev.yml up --build
```

This starts:
- API server at `http://localhost:8000`
- Frontend at `http://localhost:3000`
- PostgreSQL at `localhost:5432`
- Redis at `localhost:6379`
- MinIO at `localhost:9000` (console: `:9001`)

### 4. Access the application
- **API**: http://localhost:8000/docs (Swagger UI)
- **Frontend**: http://localhost:3000
- **MinIO Console**: http://localhost:9001

## Production Deployment

### 1. Prepare the environment
```bash
cp .env.example .env
# Set all secrets and API keys
```

### 2. Start production stack
```bash
docker compose -f docker-compose.prod.yml up -d
```

This starts:
- 3 API replicas behind nginx
- 2 worker processes
- 1 beat scheduler
- PostgreSQL with persistent storage
- Redis with persistence
- MinIO for object storage
- nginx reverse proxy

### 3. Run migrations
```bash
docker compose exec api alembic upgrade head
```

### 4. Verify deployment
```bash
docker compose -f docker-compose.prod.yml ps
curl http://localhost/health
```

## GPU Deployment

For GPU-accelerated AI processing (NVIDIA GPUs):

```bash
docker compose -f docker-compose.gpu.yml up --build
```

Requires:
- NVIDIA Container Toolkit installed
- NVIDIA driver 535+
- GPU-enabled Docker

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Required | PostgreSQL connection string |
| `REDIS_URL` | Required | Redis connection string |
| `SECRET_KEY` | Required | JWT signing secret |
| `JWT_SECRET` | Required | JWT secret |
| `JWT_EXPIRY_MINUTES` | 15 | Token expiry |
| `CLIPPYME_X264_CRF` | 23 | Video quality (0-51) |
| `CLIPPYME_X264_PRESET` | medium | Encoding speed |
| `OLLAMA_BASE_URL` | http://localhost:11434 | Ollama server URL |
| `OLLAMA_MODEL` | llama3 | Default Ollama model |
| `MINIO_ACCESS_KEY` | minioadmin | MinIO access key |
| `MINIO_SECRET_KEY` | minioadmin | MinIO secret key |
| `GEMINI_API_KEY` | Optional | Google Gemini API key |
| `STORAGE_TYPE` | local | Storage provider |
| `RATE_LIMIT_PER_MINUTE` | 100 | Rate limit |
| `WORKER_CONCURRENCY` | 2 | Celery worker concurrency |

### Storage Configuration

For S3/MinIO production storage:
```env
STORAGE_TYPE=s3
MINIO_ENDPOINT=your-minio-host:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
```

For local development (default):
```env
STORAGE_TYPE=local
STORAGE_PATH=./data/storage
```

## Docker Compose Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Main stack (base) |
| `docker-compose.dev.yml` | Development overrides |
| `docker-compose.prod.yml` | Production deployment |
| `docker-compose.gpu.yml` | GPU-accelerated deployment |

## Monitoring

### Health Checks
- API: `GET /health`
- PostgreSQL: `pg_isready`
- Redis: `redis-cli ping`
- MinIO: `/minio/health/live`

### Logs
```bash
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f beat
```

### Resource Usage
```bash
docker stats
```

## Scaling

### Scale API replicas
```bash
docker compose up -d --scale api=5
```

### Scale workers
```bash
docker compose up -d --scale worker=3
```

### Scale Beat scheduler
```bash
docker compose up -d --scale beat=2
```

## SSL/TLS

For production with HTTPS, configure nginx with SSL certificates:
1. Place certificates in `./nginx/ssl/`
2. Update `nginx/nginx.conf` with SSL settings
3. Update `docker-compose.prod.yml` nginx ports

## Backups

### PostgreSQL Backup
```bash
docker compose exec postgres pg_dump -U clipforge clipforge > backup.sql
```

### MinIO Backup
```bash
docker compose exec minio mc mirror /data /backup/minio
```

### Redis Backup
```bash
docker compose exec redis redis-cli BGSAVE
```

## Troubleshooting

### Common Issues

1. **Worker can't connect to Redis**: Check `REDIS_URL` and Redis is running
2. **API can't connect to PostgreSQL**: Check `DATABASE_URL` and PostgreSQL is healthy
3. **Transcription fails**: Ensure `faster-whisper` model is downloaded
4. **FFmpeg not found**: Ensure FFmpeg is installed on the worker
5. **Port already in use**: Check if another service uses port 8000, 3000, or 5432

### Useful Commands
```bash
# Restart all services
docker compose restart

# View API logs
docker compose logs api

# Run migrations
docker compose exec api alembic upgrade head

# Run tests
docker compose exec api pytest tests/

# Access API shell
docker compose exec api python -c "from api.app import app"
```

## Security Notes

- Change all default passwords and secrets
- Use `.env` file, never commit it
- Restrict database and Redis ports to internal network
- Use HTTPS in production
- Set `DEBUG=false` in production
- Use strong `SECRET_KEY` and `JWT_SECRET`
- Implement proper authentication and authorization
- Validate all file uploads
- Never run containers as root

---

*Last updated: September 24, 2026*