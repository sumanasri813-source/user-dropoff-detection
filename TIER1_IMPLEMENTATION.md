# TIER 1 Implementation Guide - Advanced Error Handling & Validation

## ✅ What Was Implemented

### 1. **Advanced Error Handling** (`src/utils/errors.py`)

**Features:**
- ✅ Standardized error codes (20+ predefined codes)
- ✅ Structured error responses with JSON serialization
- ✅ Custom exception hierarchy for business logic
- ✅ Error context propagation (request ID, details)
- ✅ Automatic logging of all errors

**Error Types:**
```python
- ValidationError: Input validation failures
- MissingFieldError: Required fields missing
- DatabaseError/QueryError: Database operation failures
- ModelError/ModelLoadError/PredictionError: ML model issues
- AuthenticationError: Authentication/authorization failures
- RateLimitError: Rate limiting violations
- CircuitBreakerError: Service degradation protection
- TimeoutError: Operation timeouts
```

**Usage Example:**
```python
from src.utils.errors import ValidationError

try:
    if not is_valid(data):
        raise ValidationError("Invalid user data", details={"field": "email"})
except ValidationError as e:
    api_error = handle_error(e, request_id="req-123")
    return jsonify(api_error.to_dict()), api_error.status_code
```

---

### 2. **Input Validation with Pydantic** (`src/utils/schemas.py`)

**Features:**
- ✅ Type-safe request models
- ✅ Automatic validation & error messages
- ✅ Range constraints (min/max values)
- ✅ Enum validation for categorical fields
- ✅ Optional fields with smart defaults
- ✅ Auto-generated API documentation

**Models Implemented:**
- `PredictionInputModel`: Single prediction with 9 fields
- `BatchPredictionInputModel`: Batch scoring (1-10,000 records)
- `UserCreateModel`: User creation with validation
- `UserUpdateModel`: Partial user updates
- `HealthCheckResponse`: Health check response schema
- `PredictionResponse`: Standardized prediction output
- `ErrorResponse`: Structured error responses

**Usage Example:**
```python
from src.utils.schemas import PredictionInputModel, validate_input

# Automatic validation
prediction_request = validate_input(request_data, PredictionInputModel)
# Returns validated model or raises ValidationError
```

---

### 3. **Circuit Breaker Pattern** (`src/utils/resilience.py`)

**Features:**
- ✅ Three states: CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing)
- ✅ Configurable failure/success thresholds
- ✅ Auto-recovery timeout
- ✅ Prevents cascading failures
- ✅ Thread-safe implementation

**States:**
```
CLOSED    → Normal operation, requests pass through
           ↓ (N failures)
OPEN      → Failing, reject requests immediately
           ↓ (timeout elapsed)
HALF_OPEN → Testing recovery, allow limited requests
           ↓ (success threshold met)
CLOSED    → Recovered, resume normal operation
```

**Usage Example:**
```python
from src.utils.resilience import get_circuit_breaker, with_circuit_breaker

# Manual use
breaker = get_circuit_breaker("database", failure_threshold=5)
try:
    result = breaker.call(database_query)
except CircuitBreakerError:
    # Service temporarily unavailable
    use_fallback()

# Decorator use
@with_circuit_breaker("api-service")
def call_external_api():
    return requests.get("https://api.example.com")
```

---

### 4. **Rate Limiting** (`src/utils/resilience.py`)

**Features:**
- ✅ Token bucket algorithm (sliding window)
- ✅ Per-key rate limiting (API keys, IPs)
- ✅ Configurable limits and windows
- ✅ O(1) amortized lookup
- ✅ Thread-safe

**Configuration:**
```python
# 100 requests per 60 seconds per API key
rate_limiter = PerKeyRateLimiter(max_requests=100, window_seconds=60.0)
```

**API Response on Limit Exceeded:**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded: 100 requests per 60s",
    "timestamp": "2026-04-20T10:00:00Z"
  },
  "request_id": "req-abc123"
}
```

---

### 5. **Enhanced Flask API Integration**

**Changes to `src/api/app.py`:**
- ✅ Added rate limiting to all authenticated endpoints
- ✅ Advanced error handler with proper HTTP status codes
- ✅ Structured error responses for all error types
- ✅ Rate limiting enforcement in before_request hook

**Error Handler Flow:**
```
Request → before_request (rate limit check)
        → Route handler
        → Exception raised
        → Error handler (converts to APIError)
        → JSON response with proper HTTP status
        → Metrics collection (counter increment)
```

---

## **HTTP Status Codes**

| Code | Error Type | Example |
|------|-----------|---------|
| 400 | ValidationError | Invalid input data |
| 401 | AuthenticationError | Invalid API key |
| 429 | RateLimitError | Too many requests |
| 503 | CircuitBreakerError | Service unavailable |
| 504 | TimeoutError | Operation timeout |
| 500 | Internal errors | Unexpected failures |

---

## **Testing the Implementation**

### Test Rate Limiting:
```bash
# Within 60s, make 101 requests with same API key
for i in {1..101}; do
  curl -H "X-API-Key: test-key" http://localhost:5000/health
done
# 101st request returns 429 status
```

### Test Error Handling:
```bash
# Missing required field
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"recency_days": 30}'
# Response: 400 MISSING_FIELD error

# Rate limit exceeded
# (see above)
# Response: 429 RATE_LIMIT_EXCEEDED error
```

### Test Circuit Breaker:
```python
from src.utils.resilience import get_circuit_breaker
from src.utils.errors import CircuitBreakerError

breaker = get_circuit_breaker("test-service", failure_threshold=3)

# Simulate 3 failures
for i in range(3):
    try:
        breaker.call(failing_function)
    except:
        pass

# Circuit now OPEN, next call raises immediately
try:
    breaker.call(function)
except CircuitBreakerError:
    print("Service unavailable (circuit breaker open)")
```

---

## **Benefits of TIER 1**

✅ **Reliability**: Graceful degradation prevents cascade failures  
✅ **Security**: Rate limiting + validation protects against abuse  
✅ **Observability**: Structured errors enable quick debugging  
✅ **Maintainability**: Custom exceptions clarify error conditions  
✅ **User Experience**: Consistent, informative error responses  
✅ **Scalability**: Circuit breaker prevents resource exhaustion

---

## **Next Steps (TIER 2)**

- Async request handling with FastAPI
- Redis caching for model predictions
- Database query optimization with connection pooling
- Docker containerization
- Kubernetes deployment manifests

Run: `python TIER2_implementation.py` (coming soon)
