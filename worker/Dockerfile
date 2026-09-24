FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY worker/ ./worker/
COPY api/ ./api/

EXPOSE 8000

CMD ["celery", "-A", "worker.app.celery_app", "worker", "--loglevel=info", "--concurrency=4"]