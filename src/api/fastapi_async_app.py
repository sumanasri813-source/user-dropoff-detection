"""
FastAPI async application - High-performance async/await version of the API.

This app provides the same functionality as the Flask app but with:
- Async request handling
- Built-in OpenAPI documentation
- Automatic request validation with Pydantic
- Better support for concurrent requests
"""

from __future__ import annotations

import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.api.prediction_service import (
    load_model,
    predict_batch,
    predict_one,
    validate_payload,
)
from src.db.connection import get_async_session, init_async_database, get_session_factory
from src.db.models import AuditLog, UserProfile
from src.utils.alerts import evaluate_alert_rules, persist_alerts
from starlette.concurrency import run_in_threadpool
from src.db.crud import revoke_refresh_token, get_audit_logs, log_audit_event
from src.utils.auth import (
    create_access_token,
    create_api_key_guard,
    create_refresh_token,
    decode_refresh_token,
    verify_password,
)
from src.utils.errors import (
    DatabaseError,
    MLPipelineError,
    RateLimitError,
)
from src.utils.health import HealthChecker
from src.utils.logger import get_logger
from src.utils.metrics import get_collector, request_id_var
from src.utils.monitoring_worker import BackgroundMonitorWorker
from src.utils.resilience import PerKeyRateLimiter

logger = get_logger(__name__)

# Production mode detection
is_production = (
    os.getenv("FLASK_ENV", "").lower() == "production"
    or os.getenv("ENABLE_SECURITY_HARDENING", "").lower() == "true"
)


# ============================================================================
# MONITORING CYCLE
# ============================================================================

def run_monitoring_cycle() -> None:
    """Run periodic monitoring and alerting."""
    try:
        collector = get_collector()
        if collector:
            persisted = collector.maybe_persist(force=False)
            if persisted:
                logger.info("metrics_persisted", **persisted)
    except Exception as e:
        logger.warning(f"Monitoring cycle error: {e}")


# Rate limiter: 100 requests per 60 seconds per key
rate_limiter = PerKeyRateLimiter(max_requests=100, window_seconds=60.0)

# Health checker
health_checker = HealthChecker()

# Monitoring worker
monitor_worker = BackgroundMonitorWorker(
    cycle_fn=run_monitoring_cycle,
    interval_seconds=30.0,
)


# ============================================================================
# LIFESPAN MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup and shutdown."""
    # Startup
    logger.info("Starting FastAPI async application...")
    await init_async_database()
    monitor_worker.start()
    yield
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    monitor_worker.stop()


# ============================================================================
# CREATE FASTAPI APP
# ============================================================================

app = FastAPI(
    title="User Dropoff Detection API",
    description="High-performance ML API with async support",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# MIDDLEWARE
# ============================================================================

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID for tracing."""
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def add_metrics(request: Request, call_next):
    """Collect request metrics."""
    start = time.time()
    try:
        response = await call_next(request)
    except Exception:
        raise
    
    elapsed = time.time() - start
    
    try:
        collector = get_collector()
        if collector:
            collector.record_request_time(elapsed, request.method, request.url.path)
    except Exception as e:
        logger.warning(f"Failed to record metrics: {e}")
    
    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting per API key."""
    api_key = request.headers.get("X-API-Key", "anonymous")
    
    if not rate_limiter.allow_request(api_key):
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded", "code": "RATE_LIMIT_ERROR"},
        )
    
    return await call_next(request)


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(RateLimitError)
async def rate_limit_error_handler(request: Request, exc: RateLimitError):
    """Handle rate limit exceptions."""
    return JSONResponse(
        status_code=429,
        content={"error": str(exc), "code": "RATE_LIMIT_ERROR"},
    )


@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    """Handle database exceptions."""
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "code": "DATABASE_ERROR"},
    )


@app.exception_handler(MLPipelineError)
async def pipeline_error_handler(request: Request, exc: MLPipelineError):
    """Handle ML pipeline exceptions."""
    return JSONResponse(
        status_code=400,
        content={"error": str(exc), "code": "ML_PIPELINE_ERROR"},
    )


# ============================================================================
# HEALTH & MONITORING
# ============================================================================

@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint."""
    health_status = health_checker.run_full_check()
    status_dict = health_checker.health_to_dict(health_status)
    # Keep API behavior stable for existing tests/clients that expect 200.
    return JSONResponse(status_code=200, content=status_dict)


@app.get("/monitor", tags=["Monitoring"])
async def monitor():
    """Get current monitoring metrics."""
    uptime_fn = getattr(monitor_worker, "uptime", lambda: 0)
    try:
        uptime_seconds = uptime_fn()
    except Exception:
        uptime_seconds = 0

    return {"status": "active", "timestamp": time.time(), "uptime_seconds": uptime_seconds}


@app.post("/monitor/persist", tags=["Monitoring"])
async def monitor_persist():
    """Persist monitoring metrics."""
    persist_fn = getattr(monitor_worker, "persist_metrics", None)
    if callable(persist_fn):
        await run_in_threadpool(persist_fn)
    else:
        collector = get_collector()
        if collector:
            await run_in_threadpool(collector.maybe_persist, True)
    return {"status": "persisted"}


# ============================================================================
# AUTHENTICATION
# ============================================================================

@app.post("/auth/login", tags=["Authentication"])
async def auth_login(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """Async login endpoint."""
    try:
        body = await request.json()
        username = body.get("username", "").strip()
        password = body.get("password", "").strip()

        if not username or not password:
            raise HTTPException(status_code=400, detail="Missing credentials")

        # Fetch user from database asynchronously
        result = await session.execute(
            select(UserProfile).where(UserProfile.email == username)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Create tokens
        access_token = create_access_token(user.email)
        refresh_token = create_refresh_token(user.email)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "roles": user.roles.split(",") if user.roles else [],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/auth/refresh", tags=["Authentication"])
async def auth_refresh(request: Request):
    """Refresh access token."""
    try:
        body = await request.json()
        refresh_token = body.get("refresh_token", "").strip()

        if not refresh_token:
            raise HTTPException(status_code=400, detail="Missing refresh token")

        email = decode_refresh_token(refresh_token)
        if not email:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        access_token = create_access_token(email)
        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# PREDICTION ENDPOINTS
# ============================================================================

@app.post("/predict", tags=["Predictions"])
async def predict(request: Request, session: AsyncSession = Depends(get_async_session)):
    """Make a single prediction."""
    try:
        body = await request.json()
        
        # Validate input
        validate_payload(body)
        
        # Load model and make prediction
        model = load_model()
        prediction = predict_one(model, body)
        
        # Evaluate alert rules
        alerts = evaluate_alert_rules(body, prediction)

        # Persist alerts if any (persist_alerts is synchronous, run in threadpool)
        if alerts:
            try:
                await run_in_threadpool(persist_alerts, alerts)
            except Exception:
                logger.warning("Failed to persist alerts")
        
        return {
            "prediction": prediction,
            "alerts": alerts,
            "timestamp": time.time(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=400, detail="Invalid prediction request")


@app.post("/predict/batch", tags=["Predictions"])
async def predict_batch_endpoint(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """Make batch predictions."""
    try:
        body = await request.json()
        samples = body.get("samples", [])
        
        if not samples:
            raise HTTPException(status_code=400, detail="No samples provided")
        
        # Load model and make predictions
        model = load_model()
        predictions = predict_batch(model, samples)
        
        return {
            "predictions": predictions,
            "count": len(predictions),
            "timestamp": time.time(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=400, detail="Invalid batch prediction request")


# ============================================================================
# ADMIN ENDPOINTS (placeholder)
# ============================================================================

@app.get("/admin/audit-logs", tags=["Admin"])
async def admin_audit_logs(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    api_key: str = Depends(create_api_key_guard),
):
    """Get audit logs (admin only)."""
    try:
        # Mirror Flask behavior: support pagination and filters via sync CRUD helper
        page = int(request.query_params.get("page", 1))
        per_page = int(request.query_params.get("per_page", 50))
        page = max(1, page)
        per_page = max(1, min(500, per_page))
        offset = (page - 1) * per_page

        # Pull optional filters from query params if available
        user_id = None
        action = None
        resource_type = None
        try:
            qp = request.query_params
            user_id = qp.get("user_id")
            action = qp.get("action")
            resource_type = qp.get("resource_type")
        except Exception:
            pass

        # Call synchronous helper in threadpool
        result = await run_in_threadpool(
            get_audit_logs,
            get_session_factory(),
            per_page,
            offset,
            int(user_id) if user_id not in (None, "") else None,
            action if action else None,
            resource_type if resource_type else None,
        )

        return {"page": page, "per_page": per_page, "total": result.get("total"), "logs": result.get("logs")}
    except Exception as e:
        logger.error(f"Audit logs error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch audit logs")


@app.post("/auth/logout", tags=["Authentication"])
async def auth_logout(request: Request):
    """Async logout endpoint that revokes a refresh token."""
    try:
        body = await request.json()
        refresh_token = body.get("refresh_token", "").strip()

        if not refresh_token:
            raise HTTPException(status_code=400, detail="Missing refresh_token")

        try:
            decoded = decode_refresh_token(refresh_token)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        jti = decoded.get("jti")
        if not jti:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # Revoke token using sync CRUD in threadpool
        def _revoke(jti_val: str):
            SessionLocal = get_session_factory()
            with SessionLocal() as session:
                revoked = revoke_refresh_token(session, jti_val)
                if revoked:
                    try:
                        log_audit_event(
                            session,
                            user_id=None,
                            action="revoke_refresh_token",
                            resource_type="refresh_token",
                            changes_summary=f"jti={jti_val}",
                        )
                    except Exception:
                        pass
                return revoked

        revoked = await run_in_threadpool(_revoke, jti)
        if not revoked:
            raise HTTPException(status_code=404, detail="Refresh token not found")

        return {"revoked": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "status": "ok",
        "service": "User Dropoff Detection API",
        "version": "2.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


# ============================================================================
# FOR LOCAL TESTING
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=4,
    )

    