#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose-full.yml}"
API_URL="${API_URL:-http://127.0.0.1:8000}"
START_TIMEOUT_SECONDS="${START_TIMEOUT_SECONDS:-120}"

cd "$ROOT_DIR"

echo "Starting staging deployment from: $ROOT_DIR"
echo "Using compose file: $COMPOSE_FILE"

export APP_ENV="${APP_ENV:-staging}"
export FLASK_ENV="${FLASK_ENV:-production}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"

if [[ -f .env ]]; then
  echo "Loading optional .env"
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if docker compose -f "$COMPOSE_FILE" up -d --build postgres redis api; then
  echo "Compose stack started. Waiting for API health at $API_URL/health"
else
  echo "Failed to start staging stack" >&2
  exit 1
fi

end_time=$((SECONDS + START_TIMEOUT_SECONDS))
while (( SECONDS < end_time )); do
  if curl -fsS "$API_URL/health" >/dev/null; then
    echo "Staging API is healthy at $API_URL"
    exit 0
  fi
  sleep 3
done

echo "Timed out waiting for API health at $API_URL/health" >&2
exit 1
