#!/usr/bin/env bash
set -euo pipefail

# Simple startup script for systemd or container use.
# Validates required env vars then starts the app via gunicorn.

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

echo "Validating environment..."
python startup/env_validator.py

echo "Starting application with gunicorn..."
exec gunicorn -w 4 -b 0.0.0.0:${PORT:-8000} "src.api.app:app"
