# Docker entrypoint for API
#!/bin/bash
set -e

# Wait for database
echo "Waiting for PostgreSQL..."
while ! pg_isready -h postgres -p 5432 -U clipforge; do
  sleep 1
done

# Wait for Redis
echo "Waiting for Redis..."
while ! redis-cli -h redis ping; do
  sleep 1
done

# Run migrations
echo "Running database migrations..."
cd /app/api && alembic upgrade head

# Start the server
echo "Starting ClipForge API..."
exec uvicorn api.app.main:app --host 0.0.0.0 --port 8000 --workers 4
