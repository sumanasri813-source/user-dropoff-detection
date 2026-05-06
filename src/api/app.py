from __future__ import annotations

import atexit
import os
import time
import uuid
from functools import wraps
from typing import Any, Dict

from flask import (Flask, g, jsonify, make_response, redirect, render_template,
                   request, send_from_directory)
from flask import session as flask_session
from flask import url_for
from jose import JWTError
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from src.api.prediction_service import (load_decision_threshold, load_model,
                                        load_risk_levels, predict_batch,
                                        predict_one, validate_payload)
from src.db.connection import get_session_factory, init_database
from src.db.crud import (create_prediction_record, create_user, delete_user,
                         get_audit_logs, get_refresh_token_record, get_user,
                         list_predictions, list_users, revoke_refresh_token,
                         update_user)
from src.db.models import UserProfile
from src.utils.alerts import evaluate_alert_rules, persist_alerts
from src.utils.auth import (create_access_token, create_api_key_guard,
                            create_refresh_token, create_token_or_key_guard,
                            decode_access_token, decode_refresh_token,
                            load_jwt_config, load_security_config,
                            load_session_secret_key, require_role,
                            verify_password)
from src.utils.health import HealthChecker
from src.utils.logger import get_logger
from src.utils.metrics import get_collector, request_id_var
from src.utils.monitoring_worker import BackgroundMonitorWorker

try:
    import sentry_sdk  # type: ignore
    from sentry_sdk.integrations.flask import FlaskIntegration  # type: ignore
except Exception:
    sentry_sdk = None
from src.utils.errors import (DatabaseError, MLPipelineError, RateLimitError,
                              handle_error)
from src.utils.resilience import PerKeyRateLimiter, with_circuit_breaker
from src.utils.runtime_config import (load_api_config, load_model_path,
                                      load_monitoring_config)

# production mode detection for security hardening
is_production = (
    os.getenv("FLASK_ENV", "").lower() == "production"
    or os.getenv("ENABLE_SECURITY_HARDENING", "").lower() == "true"
)

# Mount public docs at /docs (served from docs/public)
docs_public_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "docs", "public")
)
templates_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "templates")
)
try:
    os.makedirs(docs_public_dir, exist_ok=True)
except Exception:
    pass

app = Flask(
    __name__,
    static_folder=docs_public_dir,
    static_url_path="/docs",
    template_folder=templates_dir,
)

app.secret_key = load_session_secret_key()
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=is_production,
    SESSION_REFRESH_EACH_REQUEST=True,
)
logger = get_logger("api")
collector = get_collector()

# Initialize Sentry if configured
SENTRY_DSN = os.getenv("SENTRY_DSN")
SENTRY_TRACES_SAMPLE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0"))
if SENTRY_DSN and sentry_sdk is not None:
    try:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[FlaskIntegration()],
            traces_sample_rate=SENTRY_TRACES_SAMPLE,
        )
        logger.info("sentry_initialized")
    except Exception:
        logger.error("sentry_init_failed")

# Rate limiter: 100 requests per 60 seconds per API key
rate_limiter = PerKeyRateLimiter(max_requests=100, window_seconds=60.0)

model: Any = None
threshold: float = 0.5
risk_levels: Dict[str, float] = {"high": 0.7, "medium": 0.4, "low": 0.0}
monitor_worker: BackgroundMonitorWorker | None = None
alert_throttle_minutes: int = 15
require_auth: bool = False
api_key: str | None = None
SessionLocal = get_session_factory()


require_auth, api_key = load_security_config("config.yaml")
require_api_key = create_api_key_guard(lambda: (require_auth, api_key))
require_token_or_key = create_token_or_key_guard(lambda: (require_auth, api_key))


def _parse_roles(raw_roles: Any) -> list[str]:
    if not raw_roles:
        return []
    if isinstance(raw_roles, str):
        return [role.strip() for role in raw_roles.split(",") if role.strip()]
    if isinstance(raw_roles, list):
        return [str(role).strip() for role in raw_roles if str(role).strip()]
    return [str(raw_roles).strip()] if str(raw_roles).strip() else []


def _admin_session_is_authenticated() -> bool:
    return bool(flask_session.get("admin_authenticated")) and "admin" in _parse_roles(
        flask_session.get("admin_roles")
    )


def _set_admin_csrf_cookie(response):
    try:
        from src.utils.security import generate_csrf_token

        csrf_token = generate_csrf_token()
        response.set_cookie(
            "XSRF-TOKEN",
            csrf_token,
            httponly=False,
            secure=is_production,
            samesite="Lax",
        )
    except Exception:
        pass
    return response


def _request_has_admin_bearer() -> bool:
    auth_hdr = request.headers.get("Authorization", "")
    if not auth_hdr.startswith("Bearer "):
        return False

    token = auth_hdr.split(" ", 1)[1].strip()
    try:
        payload = decode_access_token(token)
    except Exception:
        return False

    roles = _parse_roles(payload.get("roles", []))
    if "admin" not in roles:
        return False

    g.token_subject = payload.get("sub")
    return True


def _render_admin_dashboard_response(
    page: int,
    per_page: int,
    user_id: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
):
    offset = (page - 1) * per_page
    with SessionLocal() as session:
        result = get_audit_logs(
            session,
            limit=per_page,
            offset=offset,
            user_id=int(user_id) if user_id is not None and user_id != "" else None,
            action=action if action else None,
            resource_type=resource_type if resource_type else None,
        )

    try:
        from src.utils.security import generate_csrf_token

        csrf_token = generate_csrf_token()
    except Exception:
        csrf_token = None

    resp = make_response(
        render_template(
            "admin_audit.html",
            admin_authenticated=True,
            logs=result["logs"],
            page=page,
            per_page=per_page,
            total=result.get("total", 0),
            user_id=user_id or "",
            action_filter=action or "",
            resource_filter=resource_type or "",
        )
    )
    if csrf_token:
        secure_cookie = True if is_production else False
        resp.set_cookie(
            "XSRF-TOKEN",
            csrf_token,
            httponly=False,
            secure=secure_cookie,
            samesite="Lax",
        )
    return resp


def _render_admin_login_response(message: str | None = None):
    return render_template(
        "admin_audit.html",
        admin_authenticated=False,
        login_message=message,
        logs=[],
        page=1,
        per_page=50,
        total=0,
        user_id="",
        action_filter="",
        resource_filter="",
    )


def require_admin_access(view_fn):
    @wraps(view_fn)
    def wrapped(*args, **kwargs):
        if _admin_session_is_authenticated():
            g.admin_auth_source = "session"
            g.token_subject = flask_session.get("admin_user_id")
            return view_fn(*args, **kwargs)

        if not require_auth:
            return view_fn(*args, **kwargs)

        api_key_header = request.headers.get("X-API-Key", "").strip()
        if api_key and api_key_header == api_key:
            g.admin_auth_source = "api_key"
            return view_fn(*args, **kwargs)

        if _request_has_admin_bearer():
            g.admin_auth_source = "bearer"
            return view_fn(*args, **kwargs)

        return (
            jsonify(
                {
                    "error": "Unauthorized. Missing admin session, API key, or Bearer token."
                }
            ),
            401,
        )

    return wrapped


def run_monitoring_cycle() -> None:
    """Run periodic monitoring and alerting. O(k) where k=small constant metrics operations."""
    persisted = collector.maybe_persist(force=False)
    if persisted:
        logger.info("metrics_persisted", **persisted)

    # Efficient health check - results cached internally by HealthChecker
    health_status = HealthChecker.run_full_check().status
    alerts = evaluate_alert_rules(
        collector.get_api_snapshot(), health_status=health_status
    )
    alert_path = persist_alerts(alerts, throttle_minutes=alert_throttle_minutes)
    if alert_path and alerts:
        # In development/local runs we prefer INFO to avoid noisy WARNINGs.
        if is_production:
            logger.warning(
                "alerts_triggered", alert_count=len(alerts), alert_path=alert_path
            )
        else:
            logger.info(
                "alerts_triggered", alert_count=len(alerts), alert_path=alert_path
            )
    # Cleanup expired refresh tokens periodically (best-effort)
    try:
        from src.db.crud import (cleanup_expired_refresh_tokens,
                                 cleanup_old_audit_logs)

        with SessionLocal() as session:
            removed = cleanup_expired_refresh_tokens(session)
            if removed:
                logger.info("cleanup_expired_refresh_tokens", removed=removed)
            # retention days from env or default 90
            retention = int(os.getenv("AUDIT_RETENTION_DAYS", "90"))
            removed_audit = cleanup_old_audit_logs(session, retention_days=retention)
            if removed_audit:
                logger.info(
                    "cleanup_old_audit_logs",
                    removed=removed_audit,
                    retention_days=retention,
                )
    except Exception as exc:
        logger.error("cleanup_tokens_failed", error=str(exc))


def start_monitoring_worker(interval_seconds: float = 30.0) -> None:
    global monitor_worker
    if monitor_worker and monitor_worker.is_running():
        return

    monitor_worker = BackgroundMonitorWorker(
        cycle_fn=run_monitoring_cycle, interval_seconds=interval_seconds
    )
    monitor_worker.start()


def stop_monitoring_worker() -> None:
    global monitor_worker
    if monitor_worker and monitor_worker.is_running():
        monitor_worker.stop(timeout_seconds=5.0)


atexit.register(stop_monitoring_worker)


@app.before_request
def before_request_hooks() -> None:
    """Pre-request initialization with rate limiting. O(1) - model cached, rate limiting O(1) amortized."""
    global model, threshold, risk_levels

    g.request_start = time.perf_counter()
    g.request_id = str(uuid.uuid4())
    request_id_var.set(g.request_id)
    # If Sentry is enabled, attach the request id for easier correlation
    try:
        if sentry_sdk is not None:
            sentry_sdk.set_tag("request_id", g.request_id)
    except Exception:
        pass

    # Rate limiting: check API key quota - O(1) amortized
    if require_auth:
        api_key_header = request.headers.get("X-API-Key", "anonymous")
        try:
            rate_limiter.allow_request(api_key_header)
        except RateLimitError:
            # This will be caught by the error handler
            raise

    # Lazy load model on first request only - subsequent calls O(1)
    if model is None:
        model = load_model(load_model_path())
        threshold = load_decision_threshold()
        risk_levels = load_risk_levels()

    # O(1) counter increments
    collector.increment_counter("api_requests_total")
    collector.increment_counter(f"api_requests_{request.method}_{request.path}")


@app.after_request
def after_request_hooks(response):
    """Post-request monitoring. O(1) - constant time metric recording and logging."""
    start = getattr(g, "request_start", None)
    latency_ms = 0.0
    if start is not None:
        latency_ms = (time.perf_counter() - start) * 1000.0
        collector.record_latency(latency_ms=latency_ms, endpoint=request.path)

    # O(1) status code grouping
    status_group = f"api_status_{response.status_code // 100}xx"
    collector.increment_counter(status_group)

    # O(1) logging with pre-computed values
    logger.info(
        "request_completed",
        request_id=getattr(g, "request_id", ""),
        method=request.method,
        path=request.path,
        status_code=response.status_code,
        latency_ms=round(latency_ms, 3),
    )

    try:
        # Don't run the full monitoring cycle on every request when a background
        # monitor worker is already running — this avoids duplicate alert
        # evaluation and noisy repeated `alerts_triggered` log entries.
        if not (monitor_worker and monitor_worker.is_running()):
            run_monitoring_cycle()
    except Exception as monitor_exc:
        logger.error("monitoring_hook_failed", error=str(monitor_exc))

    # Add security headers for admin routes
    try:
        if request.path.startswith("/admin/"):
            response.headers.setdefault("X-Frame-Options", "DENY")
            response.headers.setdefault("X-Content-Type-Options", "nosniff")
            response.headers.setdefault("Referrer-Policy", "no-referrer")
            response.headers.setdefault(
                "Permissions-Policy", "geolocation=(), microphone=()"
            )
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none';",
            )
            # Set HSTS only in production - requires HTTPS in production deployment
            if is_production:
                response.headers.setdefault(
                    "Strict-Transport-Security",
                    "max-age=31536000; includeSubDomains; preload",
                )
    except Exception:
        pass

    return response


@app.errorhandler(Exception)
def handle_exception(exc: Exception):
    """
    Advanced error handler with structured responses.
    O(1) - constant time error mapping and logging.
    """
    request_id = getattr(g, "request_id", "")

    # Preserve Flask/Werkzeug HTTP semantics (e.g., 404/405) instead of mapping to 500.
    if isinstance(exc, HTTPException):
        code = int(getattr(exc, "code", 500) or 500)
        if code >= 500:
            collector.increment_counter("api_unhandled_exceptions")
        else:
            collector.increment_counter("api_http_exceptions")
        return (
            jsonify(
                {
                    "error": {
                        "code": "HTTP_ERROR",
                        "message": str(getattr(exc, "description", str(exc))),
                        "details": {
                            "error_type": type(exc).__name__,
                            "status_code": code,
                        },
                    },
                    "request_id": request_id,
                }
            ),
            code,
        )

    # Handle rate limiting errors separately
    if isinstance(exc, RateLimitError):
        collector.increment_counter("api_rate_limited")
        api_error = handle_error(exc, request_id)
        return jsonify(api_error.to_dict()), api_error.status_code

    # Handle custom ML errors
    if isinstance(exc, MLPipelineError):
        collector.increment_counter("api_validation_errors")
        api_error = handle_error(exc, request_id)
        return jsonify(api_error.to_dict()), api_error.status_code

    # Handle database integrity errors
    if isinstance(exc, IntegrityError):
        collector.increment_counter("api_database_errors")
        db_error = DatabaseError("Database constraint violation", cause=exc)
        api_error = handle_error(db_error, request_id)
        return jsonify(api_error.to_dict()), api_error.status_code

    # Handle all other exceptions as internal errors
    collector.increment_counter("api_unhandled_exceptions")
    logger.error(
        "unhandled_exception",
        request_id=request_id,
        path=request.path if request else "",
        error_type=type(exc).__name__,
        error_message=str(exc),
        exc_info=exc,
    )
    api_error = handle_error(exc, request_id)
    return jsonify(api_error.to_dict()), api_error.status_code


@app.route("/favicon.ico", methods=["GET"])
def favicon() -> tuple:
    return ("", 204)


@app.route("/", methods=["GET"])
def root() -> tuple:
    return (
        jsonify(
            {
                "status": "ok",
                "service": "user-dropoff-detection-api",
                "health": "/health",
                "predict": "/predict",
                "predict_batch": "/predict-batch",
                "monitor": "/monitor",
            }
        ),
        200,
    )


@app.route("/health", methods=["GET"])
@require_api_key
def health() -> tuple:
    health_status = HealthChecker.run_full_check()
    health_payload = HealthChecker.health_to_dict(health_status)
    monitor_snapshot = collector.get_api_snapshot()

    db_health = {"connected": False, "error": None}
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        db_health["connected"] = True
    except Exception as db_exc:
        db_health["error"] = str(db_exc)

    response = {
        "status": "ok" if health_payload.get("status") != "unhealthy" else "error",
        "model_loaded": model is not None,
        "threshold": threshold,
        "health": health_payload,
        "database": db_health,
        "monitoring": monitor_snapshot,
        "worker": {
            "running": bool(monitor_worker and monitor_worker.is_running()),
        },
    }

    logger.info(
        "health_checked",
        health_status=health_payload.get("status"),
        model_loaded=model is not None,
    )
    return jsonify(response), (
        200 if health_payload.get("status") != "unhealthy" else 503
    )


@app.route("/monitor", methods=["GET"])
@require_api_key
def monitor() -> tuple:
    return jsonify(collector.get_api_snapshot()), 200


@app.route("/monitor/persist", methods=["POST"])
@require_api_key
def monitor_persist() -> tuple:
    persisted = collector.maybe_persist(force=True)
    return jsonify({"persisted": bool(persisted), "paths": persisted or {}}), 200


@app.route("/auth/login", methods=["POST"])
def auth_login() -> tuple:
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    identifier = payload.get("external_user_id") or payload.get("email")
    password = payload.get("password")

    if not identifier or not password:
        return jsonify({"error": "Provide external_user_id/email and password."}), 400

    with SessionLocal() as session:
        # attempt to find by external_user_id first, then email
        user = (
            session.query(UserProfile)
            .filter(
                (UserProfile.external_user_id == str(identifier))
                | (UserProfile.email == str(identifier))
            )
            .first()
        )

        if not user or not getattr(user, "password_hash", None):
            return jsonify({"error": "Invalid credentials."}), 401

        if not verify_password(str(password), user.password_hash):
            return jsonify({"error": "Invalid credentials."}), 401

        # include roles claim if present
        roles_claim = []
        if getattr(user, "roles", None):
            if isinstance(user.roles, str):
                roles_claim = [r.strip() for r in user.roles.split(",") if r.strip()]

        access = create_access_token(
            subject=str(user.id), additional_claims={"roles": roles_claim}
        )
        refresh = create_refresh_token(user_id=user.id)
        return (
            jsonify(
                {
                    "access_token": access,
                    "token_type": "bearer",
                    "refresh_token": refresh,
                }
            ),
            200,
        )


@app.route("/protected", methods=["GET"])
@require_token_or_key
def protected_sample() -> tuple:
    # returns the token subject if present
    subj = getattr(g, "token_subject", None)
    return jsonify({"protected": True, "token_subject": subj}), 200


@app.route("/auth/refresh", methods=["POST"])
def auth_refresh() -> tuple:
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    token = payload.get("refresh_token")
    if not token:
        return jsonify({"error": "Missing refresh_token."}), 400

    try:
        decoded = decode_refresh_token(token)
    except JWTError:
        return jsonify({"error": "Invalid refresh token."}), 401

    jti = decoded.get("jti")
    sub = decoded.get("sub")
    if not jti or not sub:
        return jsonify({"error": "Invalid refresh token."}), 401

    with SessionLocal() as session:
        rec = get_refresh_token_record(session, jti=jti)
        if not rec or rec.revoked:
            return jsonify({"error": "Refresh token revoked or not found."}), 401

        # rotate: revoke old and issue new
        revoke_refresh_token(session, jti=jti)
        try:
            from src.db.crud import log_audit_event

            log_audit_event(
                session,
                user_id=int(sub),
                action="revoke_refresh_token",
                resource_type="refresh_token",
                changes_summary=f"jti={jti}",
            )
        except Exception:
            pass

        new_refresh = create_refresh_token(user_id=int(sub))
        new_access = create_access_token(subject=str(sub))
        return jsonify({"access_token": new_access, "refresh_token": new_refresh}), 200


@app.route("/auth/logout", methods=["POST"])
def auth_logout() -> tuple:
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    token = payload.get("refresh_token")
    if not token:
        return jsonify({"error": "Missing refresh_token."}), 400

    try:
        decoded = decode_refresh_token(token)
    except JWTError:
        return jsonify({"error": "Invalid refresh token."}), 401

    jti = decoded.get("jti")
    if not jti:
        return jsonify({"error": "Invalid refresh token."}), 401

    with SessionLocal() as session:
        revoked = revoke_refresh_token(session, jti=jti)
        if not revoked:
            return jsonify({"error": "Refresh token not found."}), 404
        try:
            from src.db.crud import log_audit_event

            log_audit_event(
                session,
                user_id=(
                    None
                    if not getattr(g, "token_subject", None)
                    else int(g.token_subject)
                ),
                action="revoke_refresh_token",
                resource_type="refresh_token",
                changes_summary=f"jti={jti}",
            )
        except Exception:
            pass
        return jsonify({"revoked": True}), 200


@app.route("/admin/login", methods=["POST"])
def admin_login() -> tuple:
    payload: Dict[str, Any] = (
        request.get_json(silent=True) or request.form.to_dict() or {}
    )
    identifier = (
        payload.get("external_user_id")
        or payload.get("email")
        or payload.get("username")
    )
    password = payload.get("password")

    if not identifier or not password:
        return jsonify({"error": "Provide username/email and password."}), 400

    with SessionLocal() as session:
        user = (
            session.query(UserProfile)
            .filter(
                (UserProfile.external_user_id == str(identifier))
                | (UserProfile.email == str(identifier))
            )
            .first()
        )

        if not user or not getattr(user, "password_hash", None):
            return jsonify({"error": "Invalid credentials."}), 401

        if not verify_password(str(password), user.password_hash):
            return jsonify({"error": "Invalid credentials."}), 401

        roles = _parse_roles(getattr(user, "roles", None))
        if "admin" not in roles:
            return jsonify({"error": "Forbidden. Admin role required."}), 403

        flask_session.clear()
        flask_session["admin_authenticated"] = True
        flask_session["admin_user_id"] = user.id
        flask_session["admin_roles"] = roles
        flask_session.permanent = True

    return jsonify({"authenticated": True, "admin": True, "user_id": user.id}), 200


@app.route("/admin/logout", methods=["POST"])
def admin_logout() -> tuple:
    flask_session.clear()
    response = jsonify({"logged_out": True})
    response.delete_cookie("XSRF-TOKEN")
    return response, 200


@app.route("/admin/audit-logs", methods=["GET"])
@require_admin_access
def admin_audit_logs() -> tuple:
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    page = max(1, page)
    per_page = max(1, min(500, per_page))
    offset = (page - 1) * per_page

    # optional filters
    user_id = request.args.get("user_id")
    action = request.args.get("action")
    resource_type = request.args.get("resource_type")

    with SessionLocal() as session:
        result = get_audit_logs(
            session,
            limit=per_page,
            offset=offset,
            user_id=int(user_id) if user_id is not None and user_id != "" else None,
            action=action if action else None,
            resource_type=resource_type if resource_type else None,
        )

    return (
        jsonify(
            {
                "page": page,
                "per_page": per_page,
                "total": result["total"],
                "logs": result["logs"],
            }
        ),
        200,
    )


@app.route("/admin/audit-logs/distinct", methods=["GET"])
@require_admin_access
def admin_audit_logs_distinct() -> tuple:
    """Return distinct values for a given field (user_id, action, resource_type) for typeahead."""
    field = request.args.get("field")
    if field not in {"user_id", "action", "resource_type"}:
        return jsonify({"error": "Invalid field"}), 400

    with SessionLocal() as session:
        if field == "user_id":
            rows = (
                session.query(AuditLog.user_id)
                .distinct()
                .order_by(AuditLog.user_id)
                .all()
            )
            values = [r[0] for r in rows if r[0] is not None]
        elif field == "action":
            rows = (
                session.query(AuditLog.action)
                .distinct()
                .order_by(AuditLog.action)
                .all()
            )
            values = [r[0] for r in rows if r[0]]
        else:
            rows = (
                session.query(AuditLog.resource_type)
                .distinct()
                .order_by(AuditLog.resource_type)
                .all()
            )
            values = [r[0] for r in rows if r[0]]

    return jsonify({"field": field, "values": values}), 200


@app.route("/admin/audit-logs/export", methods=["GET"])
@require_admin_access
def admin_audit_logs_export() -> tuple:
    """Export filtered audit logs as CSV. Uses same filters as listing endpoint."""
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 1000))
    page = max(1, page)
    per_page = max(1, min(10000, per_page))
    offset = (page - 1) * per_page

    user_id = request.args.get("user_id")
    action = request.args.get("action")
    resource_type = request.args.get("resource_type")

    with SessionLocal() as session:
        result = get_audit_logs(
            session,
            limit=per_page,
            offset=offset,
            user_id=int(user_id) if user_id is not None and user_id != "" else None,
            action=action if action else None,
            resource_type=resource_type if resource_type else None,
        )

    # build CSV
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "user_id",
            "action",
            "resource_type",
            "resource_id",
            "changes_summary",
            "created_at",
        ]
    )
    for r in result["logs"]:
        writer.writerow(
            [
                r.get("id"),
                r.get("user_id"),
                r.get("action"),
                r.get("resource_type"),
                r.get("resource_id"),
                r.get("changes_summary"),
                r.get("created_at"),
            ]
        )

    csv_data = output.getvalue()
    resp = make_response(csv_data)
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    resp.headers["Content-Disposition"] = "attachment; filename=audit_logs.csv"
    return resp


@app.route("/admin/audit-logs/viewer", methods=["GET"])
@require_admin_access
def admin_audit_logs_viewer() -> tuple:
    """Serve the static audit logs viewer HTML for admins.
    Falls back to 404 on errors. The file is located in the repository `docs/` folder.
    """
    try:
        docs_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "docs")
        )
        private_dir = os.path.join(docs_dir, "private")
        return send_from_directory(private_dir, "audit_logs_viewer.html")
    except Exception as exc:
        logger.error("serve_audit_viewer_failed", error=str(exc))
        return jsonify({"error": "Audit viewer not available."}), 404


@app.route("/admin/dashboard", methods=["GET"])
def admin_dashboard() -> tuple:
    """Admin dashboard page that embeds the audit viewer in an iframe.

    This provides a small, centralized admin UI that still uses the protected
    `admin_audit_logs_viewer` endpoint for the actual viewer payload.
    """
    try:
        if _admin_session_is_authenticated():
            page = int(request.args.get("page", 1))
            per_page = int(request.args.get("per_page", 50))
            page = max(1, page)
            per_page = max(1, min(500, per_page))
            user_id = request.args.get("user_id")
            action = request.args.get("action")
            resource_type = request.args.get("resource_type")
            return _render_admin_dashboard_response(
                page,
                per_page,
                user_id=user_id,
                action=action,
                resource_type=resource_type,
            )

        if _request_has_admin_bearer():
            page = int(request.args.get("page", 1))
            per_page = int(request.args.get("per_page", 50))
            page = max(1, page)
            per_page = max(1, min(500, per_page))
            user_id = request.args.get("user_id")
            action = request.args.get("action")
            resource_type = request.args.get("resource_type")
            return _render_admin_dashboard_response(
                page,
                per_page,
                user_id=user_id,
                action=action,
                resource_type=resource_type,
            )

        return _render_admin_login_response()
    except Exception as exc:
        logger.error("render_admin_dashboard_failed", error=str(exc))
        return jsonify({"error": "Admin dashboard not available."}), 500


@app.route("/admin/audit-logs/<int:log_id>", methods=["DELETE"])
@require_admin_access
def admin_delete_audit_log(log_id: int) -> tuple:
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    reason = payload.get("reason")
    if not reason or not isinstance(reason, str) or len(reason.strip()) < 5:
        return (
            jsonify(
                {"error": "Provide non-empty 'reason' (min 5 chars) for deletion."}
            ),
            400,
        )

    # CSRF protection: require X-CSRF-Token header with valid token
    csrf_header = request.headers.get("X-CSRF-Token", "")
    if not csrf_header:
        return jsonify({"error": "Missing CSRF token."}), 403
    try:
        from src.utils.security import validate_csrf_token

        if not validate_csrf_token(csrf_header):
            return jsonify({"error": "Invalid CSRF token."}), 403
    except Exception:
        return jsonify({"error": "CSRF validation failed."}), 403

    with SessionLocal() as session:
        from src.db.crud import delete_audit_log, log_audit_event

        success = delete_audit_log(session, log_id=log_id)
        if not success:
            return jsonify({"error": "Audit log not found."}), 404
        try:
            # Log the deletion action itself
            user_id = None
            try:
                user_id = int(getattr(g, "token_subject", None))
            except Exception:
                user_id = None
            log_audit_event(
                session,
                user_id=user_id or 0,
                action="delete_audit_log",
                resource_type="audit_log",
                resource_id=log_id,
                reason=reason,
            )
        except Exception:
            pass
        return jsonify({"deleted": True, "log_id": log_id}), 200


@app.route("/predict", methods=["POST"])
@require_token_or_key
def predict() -> tuple:
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    ok, message = validate_payload(payload)
    if not ok:
        collector.increment_counter("prediction_validation_errors")
        return (
            jsonify({"error": message, "request_id": getattr(g, "request_id", "")}),
            400,
        )

    try:
        result = predict_one(model, payload, threshold, risk_levels)
        try:
            with SessionLocal() as session:
                create_prediction_record(
                    session=session,
                    prediction_result=result,
                    request_id=getattr(g, "request_id", ""),
                    payload=payload,
                )
        except Exception as db_exc:
            logger.error("prediction_db_persist_failed", error=str(db_exc))
        return jsonify({**result, "request_id": getattr(g, "request_id", "")}), 200
    except Exception as exc:
        collector.increment_counter("prediction_runtime_errors")
        logger.error(
            "predict_failed", request_id=getattr(g, "request_id", ""), error=str(exc)
        )
        return (
            jsonify({"error": str(exc), "request_id": getattr(g, "request_id", "")}),
            400,
        )


@app.route("/users", methods=["POST"])
@require_token_or_key
def users_create() -> tuple:
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    if not payload.get("external_user_id"):
        return jsonify({"error": "Field 'external_user_id' is required."}), 400

    try:
        with SessionLocal() as session:
            row = create_user(session, payload)
        return jsonify(row), 201
    except IntegrityError:
        return jsonify({"error": "external_user_id must be unique."}), 409
    except Exception as exc:
        logger.error("users_create_failed", error=str(exc))
        return jsonify({"error": str(exc)}), 400


@app.route("/users", methods=["GET"])
@require_token_or_key
def users_list() -> tuple:
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))
    user_segment = request.args.get("user_segment")
    limit = max(1, min(1000, limit))
    offset = max(0, offset)
    with SessionLocal() as session:
        rows = list_users(
            session, limit=limit, offset=offset, user_segment=user_segment
        )
    return jsonify({"count": len(rows), "users": rows}), 200


@app.route("/users/<int:user_id>", methods=["GET"])
@require_token_or_key
def users_get(user_id: int) -> tuple:
    with SessionLocal() as session:
        row = get_user(session, user_id=user_id)
    if not row:
        return jsonify({"error": "User not found."}), 404
    return jsonify(row), 200


@app.route("/users/<int:user_id>", methods=["PUT"])
@require_token_or_key
def users_update(user_id: int) -> tuple:
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    with SessionLocal() as session:
        row = update_user(session, user_id=user_id, payload=payload)
    if not row:
        return jsonify({"error": "User not found."}), 404
    return jsonify(row), 200


@app.route("/users/<int:user_id>", methods=["DELETE"])
@require_token_or_key
@require_role("admin")
def users_delete(user_id: int) -> tuple:
    with SessionLocal() as session:
        deleted = delete_user(session, user_id=user_id)
    if not deleted:
        return jsonify({"error": "User not found."}), 404
    return jsonify({"deleted": True, "user_id": user_id}), 200


@app.route("/predictions", methods=["GET"])
@require_token_or_key
def predictions_list() -> tuple:
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))
    risk_level = request.args.get("risk_level")
    min_probability_raw = request.args.get("min_probability")
    min_probability = (
        float(min_probability_raw) if min_probability_raw is not None else None
    )
    limit = max(1, min(1000, limit))
    offset = max(0, offset)
    with SessionLocal() as session:
        rows = list_predictions(
            session,
            limit=limit,
            offset=offset,
            risk_level=risk_level,
            min_probability=min_probability,
        )
    return jsonify({"count": len(rows), "predictions": rows}), 200


@app.route("/predict-batch", methods=["POST"])
@require_token_or_key
def predict_batch_route() -> tuple:
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    records = payload.get("records", [])

    if not isinstance(records, list) or len(records) == 0:
        collector.increment_counter("prediction_batch_payload_errors")
        return (
            jsonify(
                {
                    "error": "Payload must include non-empty list field 'records'.",
                    "request_id": getattr(g, "request_id", ""),
                }
            ),
            400,
        )

    result = predict_batch(model, records, threshold, risk_levels)
    status_code = 207 if result["failed_predictions"] > 0 else 200
    return jsonify({**result, "request_id": getattr(g, "request_id", "")}), status_code


if __name__ == "__main__":
    require_auth, api_key = load_security_config("config.yaml")
    try:
        # Validate runtime environment early and fail fast if required secrets are missing.
        from startup.env_validator import validate_env

        validate_env()
    except SystemExit:
        # allow explicit sys.exit from the validator to propagate
        raise
    except Exception as e:
        logger.error("env_validator_failed", error=str(e))

    init_database()
    host, port, debug = load_api_config()
    interval_sec, throttle_min = load_monitoring_config()
    alert_throttle_minutes = throttle_min
    start_monitoring_worker(interval_seconds=interval_sec)
    logger.info(
        "api_starting",
        host=host,
        port=port,
        debug=debug,
        monitoring_interval_sec=interval_sec,
        alert_throttle_minutes=throttle_min,
    )
    app.run(host=host, port=port, debug=debug)
