# Minimal Node Gateway Adapter

This is a minimal production-API adapter example that forwards the public gateway contract to the current Python service endpoint.

## What it does

- Exposes `POST /v1/dropoff/predict` (public shape)
- Maps payload to current Python endpoint format (`/predict`)
- Forwards request to Python model service
- Maps Python response back to public response shape

## Requirements

- Node.js 18+
- Python service running at `http://localhost:5000/predict` (default)

## Run

```powershell
cd gateway/node-minimal
npm start
```

Optional environment variables:

```powershell
$env:PORT=8080
$env:PYTHON_MODEL_SERVICE_URL="http://localhost:5000/predict"
$env:MODEL_NAME="dropoff_classifier"
$env:MODEL_VERSION="2026.04.08.1"
npm start
```

## Test request

```powershell
curl -X POST http://localhost:8080/v1/dropoff/predict \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "f3b1c8a2-8c8b-4f5f-b35c-1c0a0c0f9b12",
    "user": {"user_id": "U12345", "segment": "free", "region": "north"},
    "session": {
      "session_id": "S998877",
      "timestamp_utc": "2026-04-08T10:30:00Z",
      "device_type": "mobile",
      "os_type": "android"
    },
    "features": {
      "days_signup_age": 250,
      "recency_days": 45,
      "frequency_total": 9,
      "session_duration_avg": 6.5,
      "feature_count_used": 2
    }
  }'
```

## Notes

- This adapter intentionally stays minimal and dependency-light.
- For production hardening, add auth middleware, rate limiting, retries, and structured logging.
