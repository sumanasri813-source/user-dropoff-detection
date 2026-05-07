#!/bin/bash
# Startup script for FastAPI async server

set -e

cd /workspaces/user-dropoff-detection

echo "======================================"
echo "User Dropoff Detection - FastAPI v2.0.0"
echo "======================================"
echo ""

# Check Python environment
echo "✓ Python environment configured"
PYTHON="/workspaces/user-dropoff-detection/.venv/bin/python"

# Ensure dependencies
echo "Checking dependencies..."
$PYTHON -m pip install -q aiosqlite 2>/dev/null || true

# Start FastAPI server
echo ""
echo "Starting FastAPI server on http://0.0.0.0:8000..."
echo "Press Ctrl+C to stop"
echo ""

$PYTHON -m uvicorn src.api.fastapi_async_app:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --log-level info
