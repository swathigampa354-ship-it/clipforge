# Test runner script
#!/bin/bash
set -e

echo "=== ClipForge Test Suite ==="

# Install dependencies
cd api && pip install -e . && cd ..
cd frontend && npm ci && cd ..

# Run API tests
echo "Running API tests..."
cd api && pytest tests/ -v --tb=short && cd ..

# Run frontend type check
echo "Running frontend type check..."
cd frontend && npm run typecheck && cd ..

# Run linting
echo "Running linter..."
cd api && ruff check . && cd ..

echo "=== All tests passed ==="
