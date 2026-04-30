# API Testing Guide

Complete guide for testing the User Dropoff Detection API using Postman and curl.

---

## Quick Start with Postman

### 1. Import Collection
1. Open Postman
2. Click "Import" → "Upload Files"
3. Select `Postman_Collection.json`
4. Collection loads with all test scenarios

### 2. Configure Environment
1. Create new Environment named `dropoff-api-env`
2. Add variables:
   - `base_url` = `http://127.0.0.1:5000`
   - `api_key` = `dev-local-key`

### 3. Run Tests
- Click "Run" on collection
- Select `dropoff-api-env`
- Click "Start Test Run"
- View results

---

## API Endpoints

### 1. Health Check
**Purpose**: Verify API and model status

**Request**:
```bash
curl -X GET http://127.0.0.1:5000/health
```

**Response**:
```json
{
  "status": "healthy",
  "model_status": "loaded",
  "database_status": "connected",
  "timestamp": "2024-04-26T12:30:45Z",
  "api_version": "1.0.0"
}
```

**Expected Status**: `200 OK`

---

### 2. Single Prediction
**Purpose**: Predict dropoff for one user

**Request**:
```bash
curl -X POST http://127.0.0.1:5000/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-local-key" \
  -d '{
    "days_signup_age": 180,
    "recency_days": 15,
    "frequency_total": 45,
    "session_duration_avg": 12.5,
    "feature_count_used": 8,
    "device_type": "desktop",
    "os_type": "windows",
    "user_segment": "premium",
    "region": "north",
    "user_id": 1001
  }'
```

**Response**:
```json
{
  "prediction": 0,
  "probability": 0.25,
  "risk_level": "low",
  "confidence": 0.92,
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Field Reference**:
| Field | Type | Range | Description |
|-------|------|-------|---|
| days_signup_age | integer | 30-730 | Days since signup |
| recency_days | integer | 0-120 | Days since last activity |
| frequency_total | integer | 0-200 | Total interactions |
| session_duration_avg | float | 1.0-60.0 | Avg session minutes |
| feature_count_used | integer | 1-15 | Features used |
| device_type | string | mobile, desktop, tablet | Device type |
| os_type | string | windows, mac, android, ios, linux | OS type |
| user_segment | string | free, trial, premium | Subscription tier |
| region | string | north, south, east, west | Geographic region |
| user_id | integer | >0 | Optional user ID |

**Expected Status**: `200 OK`

---

### 3. Batch Prediction
**Purpose**: Predict dropoff for multiple users

**Request**:
```bash
curl -X POST http://127.0.0.1:5000/predict-batch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-local-key" \
  -d '{
    "predictions": [
      {
        "days_signup_age": 500,
        "recency_days": 5,
        "frequency_total": 100,
        "session_duration_avg": 45.0,
        "feature_count_used": 14,
        "device_type": "desktop",
        "os_type": "windows",
        "user_segment": "premium",
        "region": "north"
      },
      {
        "days_signup_age": 45,
        "recency_days": 100,
        "frequency_total": 5,
        "session_duration_avg": 2.0,
        "feature_count_used": 1,
        "device_type": "mobile",
        "os_type": "android",
        "user_segment": "free",
        "region": "south"
      }
    ],
    "return_probabilities": true
  }'
```

**Response**:
```json
[
  {
    "prediction": 0,
    "probability": 0.15,
    "risk_level": "low",
    "confidence": 0.94,
    "request_id": "550e8400-..."
  },
  {
    "prediction": 1,
    "probability": 0.85,
    "risk_level": "high",
    "confidence": 0.91,
    "request_id": "550e8400-..."
  }
]
```

**Expected Status**: `200 OK`

---

### 4. Monitoring Metrics
**Purpose**: View API performance and usage metrics

**Request**:
```bash
curl -X GET http://127.0.0.1:5000/monitor
```

**Response**:
```json
{
  "api_requests_total": 1234,
  "api_requests_prediction": 890,
  "api_requests_batch": 120,
  "api_status_2xx": 1100,
  "api_status_4xx": 100,
  "api_status_5xx": 5,
  "uptime_seconds": 3600,
  "average_latency_ms": 45.2,
  "p99_latency_ms": 120.5
}
```

**Expected Status**: `200 OK`

---

## Error Handling

### Validation Error (Missing Field)
```bash
curl -X POST http://127.0.0.1:5000/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-local-key" \
  -d '{"days_signup_age": 500}'
```

**Response** (400 Bad Request):
```json
{
  "error": "Missing fields: recency_days, frequency_total, ...",
  "error_code": "VALIDATION_ERROR",
  "request_id": "550e8400-...",
  "details": {
    "missing_fields": ["recency_days", "frequency_total", ...]
  }
}
```

---

### Type Error
```bash
curl -X POST http://127.0.0.1:5000/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-local-key" \
  -d '{
    "days_signup_age": "not-a-number",
    "recency_days": 15,
    ...
  }'
```

**Response** (400 Bad Request):
```json
{
  "error": "Field 'days_signup_age' must be numeric.",
  "error_code": "TYPE_ERROR",
  "request_id": "550e8400-..."
}
```

---

### Out of Range Error
```bash
curl -X POST http://127.0.0.1:5000/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-local-key" \
  -d '{
    "days_signup_age": 1000,
    ...
  }'
```

**Response** (400 Bad Request):
```json
{
  "error": "Field 'days_signup_age' must be 30-730",
  "error_code": "RANGE_ERROR",
  "request_id": "550e8400-...",
  "details": {
    "field": "days_signup_age",
    "value": 1000,
    "min": 30,
    "max": 730
  }
}
```

---

### Rate Limit Error
```bash
curl -X POST http://127.0.0.1:5000/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-local-key" \
  -d '{...}' # 101st request within 60 seconds
```

**Response** (429 Too Many Requests):
```json
{
  "error": "Rate limit exceeded: 100 requests per 60 seconds",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "request_id": "550e8400-...",
  "details": {
    "limit": 100,
    "window_seconds": 60,
    "retry_after_seconds": 45
  }
}
```

---

## Test Scenarios

### Scenario 1: Low Risk User
```bash
curl -X POST http://127.0.0.1:5000/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-local-key" \
  -d '{
    "days_signup_age": 500,
    "recency_days": 5,
    "frequency_total": 100,
    "session_duration_avg": 45.0,
    "feature_count_used": 14,
    "device_type": "desktop",
    "os_type": "windows",
    "user_segment": "premium",
    "region": "north"
  }'
```

**Expected**: 
- `prediction` = 0 (will not drop off)
- `risk_level` = "low"
- `probability` < 0.4

---

### Scenario 2: High Risk User
```bash
curl -X POST http://127.0.0.1:5000/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-local-key" \
  -d '{
    "days_signup_age": 45,
    "recency_days": 100,
    "frequency_total": 5,
    "session_duration_avg": 2.0,
    "feature_count_used": 1,
    "device_type": "mobile",
    "os_type": "android",
    "user_segment": "free",
    "region": "south"
  }'
```

**Expected**:
- `prediction` = 1 (will drop off)
- `risk_level` = "high"
- `probability` > 0.7

---

### Scenario 3: Medium Risk User
```bash
curl -X POST http://127.0.0.1:5000/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-local-key" \
  -d '{
    "days_signup_age": 200,
    "recency_days": 30,
    "frequency_total": 50,
    "session_duration_avg": 20.0,
    "feature_count_used": 8,
    "device_type": "tablet",
    "os_type": "ios",
    "user_segment": "trial",
    "region": "east"
  }'
```

**Expected**:
- `risk_level` = "medium"
- `probability` between 0.4-0.7

---

## Performance Testing

### Load Test (100 concurrent requests)
```bash
# Using Apache Bench
ab -n 100 -c 10 -H "X-API-Key: dev-local-key" \
  http://127.0.0.1:5000/health

# Results
# Requests per second: ~500-1000
# Mean latency: 10-50ms
# 99th percentile: <100ms
```

### Batch Processing (1000 predictions)
```bash
curl -X POST http://127.0.0.1:5000/predict-batch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-local-key" \
  -d '{"predictions": [... 1000 items ...]}'

# Expected latency: 5-10 seconds
```

---

## Logging & Audit Trail

### View Prediction Logs
```bash
tail -f logs/api.log | grep prediction_made
```

**Log Format**:
```json
{
  "timestamp": "2024-04-26T12:30:45.123456",
  "message": "prediction_made",
  "data": {
    "user_id": 1001,
    "prediction": 0,
    "probability": 0.25,
    "risk_level": "low",
    "request_id": "550e8400-...",
    "latency_ms": 42.5
  }
}
```

### View Audit Trail
```bash
tail -f logs/audit.jsonl
```

**Audit Format** (immutable record):
```json
{
  "timestamp": "2024-04-26T12:30:45.123456",
  "request_id": "550e8400-...",
  "user_id": 1001,
  "input_features": {
    "days_signup_age": 180,
    "recency_days": 15,
    ...
  },
  "prediction": 0,
  "probability": 0.25,
  "risk_level": "low"
}
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 404 Not Found | Check endpoint URL and method |
| 400 Bad Request | Validate JSON syntax and field types |
| 401 Unauthorized | Verify `X-API-Key` header |
| 429 Too Many Requests | Wait 60 seconds, then retry |
| 500 Internal Error | Check logs: `tail -f logs/api.log` |
| Connection refused | Ensure API is running: `python -m src.api.app` |

---

## Next Steps

1. ✅ Run Postman tests
2. ✅ Verify all endpoints respond
3. ✅ Test error scenarios
4. ✅ Review logs for any issues
5. ✅ Deploy to production
