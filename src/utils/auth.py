from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Callable, Mapping, Tuple

from flask import jsonify, request
from jose import JWTError, jwt
from passlib.context import CryptContext
import uuid
from datetime import timedelta
from typing import List
from src.db.connection import get_session_factory


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def load_security_config(config_path: str = "config.yaml") -> Tuple[bool, str | None]:
    required = False
    key: str | None = None

    try:
        from src.utils.config_loader import load_config

        cfg = load_config(config_path)
        security = cfg.get("security", {}) if isinstance(cfg.get("security", {}), dict) else {}
        required = bool(security.get("require_auth", False))

        env_var_name = str(security.get("api_key_env_var", "API_KEY")).strip() or "API_KEY"
        key_from_env = os.getenv(env_var_name, "").strip()
        key_from_config = str(security.get("api_key", "")).strip()
        key = key_from_env or key_from_config or None
    except Exception:
        pass

    return required, key


def create_api_key_guard(security_state_getter: Callable[[], Tuple[bool, str | None]]):
    def guard(view_fn: Callable):
        @wraps(view_fn)
        def wrapped(*args, **kwargs):
            require_auth, api_key = security_state_getter()
            if not require_auth:
                return view_fn(*args, **kwargs)

            candidate = request.headers.get("X-API-Key", "").strip()
            if api_key and candidate == api_key:
                return view_fn(*args, **kwargs)

            return jsonify({"error": "Unauthorized. Missing or invalid X-API-Key."}), 401

        return wrapped

    return guard


def hash_password(password: str) -> str:
    """Hash a plaintext password for storage."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against its stored hash."""
    return pwd_context.verify(plain_password, password_hash)


def load_jwt_config(config_path: str = "config.yaml") -> Tuple[str, str, int]:
    """Load JWT settings from environment and optional config file."""
    secret_key = ""
    algorithm = "HS256"
    expiration_hours = 24

    try:
        from src.utils.config_loader import load_config

        cfg = load_config(config_path)
        security = cfg.get("security", {}) if isinstance(cfg.get("security", {}), dict) else {}

        secret_key = (
            str(security.get("jwt_secret_key", "")).strip()
            or str(security.get("secret_key", "")).strip()
            or str(security.get("api_key", "")).strip()
            or secret_key
        )
        algorithm = str(security.get("jwt_algorithm", algorithm)).strip() or algorithm
        expiration_hours = int(security.get("jwt_expiration_hours", expiration_hours))
    except Exception:
        pass

    env_secret_key = os.getenv("JWT_SECRET_KEY", "").strip() or os.getenv("SECRET_KEY", "").strip()
    env_algorithm = os.getenv("JWT_ALGORITHM", "").strip()
    env_expiration_hours = os.getenv("JWT_EXPIRATION_HOURS", "").strip()

    if env_secret_key:
        secret_key = env_secret_key
    if env_algorithm:
        algorithm = env_algorithm
    if env_expiration_hours:
        try:
            expiration_hours = int(env_expiration_hours)
        except ValueError:
            pass

    if not secret_key:
        secret_key = "change-me-in-production"

    return secret_key, algorithm, expiration_hours


def load_session_secret_key(config_path: str = "config.yaml") -> str:
    """Load Flask session secret separately from JWT signing secret."""
    secret_key = ""

    try:
        from src.utils.config_loader import load_config

        cfg = load_config(config_path)
        security = cfg.get("security", {}) if isinstance(cfg.get("security", {}), dict) else {}
        secret_key = str(security.get("session_secret_key", "")).strip() or secret_key
    except Exception:
        pass

    env_secret_key = os.getenv("SESSION_SECRET_KEY", "").strip() or os.getenv("FLASK_SECRET_KEY", "").strip()
    if env_secret_key:
        secret_key = env_secret_key

    if not secret_key:
        secret_key = load_jwt_config(config_path)[0]

    return secret_key


def create_access_token(
    subject: str,
    additional_claims: Mapping[str, Any] | None = None,
    expires_delta: timedelta | None = None,
    config_path: str = "config.yaml",
) -> str:
    """Create a signed JWT access token."""
    secret_key, algorithm, expiration_hours = load_jwt_config(config_path)
    now = datetime.now(timezone.utc)
    expires_at = now + (expires_delta or timedelta(hours=expiration_hours))

    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "type": "access",
    }
    if additional_claims:
        payload.update(dict(additional_claims))

    return jwt.encode(payload, secret_key, algorithm=algorithm)


def create_refresh_token(user_id: int, expires_delta: timedelta | None = None, config_path: str = "config.yaml") -> str:
    """Create a signed JWT refresh token and persist its jti in DB."""
    secret_key, algorithm, default_hours = load_jwt_config(config_path)
    now = datetime.now(timezone.utc)
    expires_at = now + (expires_delta or timedelta(days=30))
    jti = str(uuid.uuid4())

    payload = {
        "sub": str(user_id),
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "type": "refresh",
    }

    token = jwt.encode(payload, secret_key, algorithm=algorithm)

    # persist jti
    SessionLocal = get_session_factory()
    with SessionLocal() as session:
        from src.db.crud import create_refresh_token_record, log_audit_event
        create_refresh_token_record(session, user_id=user_id, jti=jti, expires_at=expires_at)
        try:
            # record audit event for issuance
            log_audit_event(session, user_id=user_id, action="issue_refresh_token", resource_type="refresh_token", resource_id=None, changes_summary=f"jti={jti}")
        except Exception:
            pass

    return token


def decode_refresh_token(token: str, config_path: str = "config.yaml") -> dict[str, Any]:
    secret_key, algorithm, _ = load_jwt_config(config_path)
    return jwt.decode(token, secret_key, algorithms=[algorithm])


def require_role(role: str):
    def decorator(view_fn: Callable):
        @wraps(view_fn)
        def wrapped(*args, **kwargs):
            # If auth is not required globally, skip role enforcement.
            try:
                from src.api.app import require_auth as _require_auth
            except Exception:
                _require_auth = False

            if not _require_auth:
                return view_fn(*args, **kwargs)

            # Expect Bearer token when auth is required
            auth_hdr = request.headers.get("Authorization", "")
            if not auth_hdr.startswith("Bearer "):
                return jsonify({"error": "Forbidden. Missing Bearer token."}), 403

            token = auth_hdr.split(" ", 1)[1].strip()
            try:
                payload = decode_access_token(token)
            except JWTError:
                return jsonify({"error": "Invalid token."}), 401

            roles = payload.get("roles", [])
            if isinstance(roles, str):
                roles = [r.strip() for r in roles.split(",") if r.strip()]

            if role not in roles:
                return jsonify({"error": "Forbidden. Insufficient role."}), 403

            return view_fn(*args, **kwargs)

        return wrapped

    return decorator


def decode_access_token(token: str, config_path: str = "config.yaml") -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    secret_key, algorithm, _ = load_jwt_config(config_path)
    return jwt.decode(token, secret_key, algorithms=[algorithm])


def get_token_subject(token: str, config_path: str = "config.yaml") -> str | None:
    """Return the token subject if decoding succeeds."""
    try:
        payload = decode_access_token(token, config_path=config_path)
    except JWTError:
        return None

    subject = payload.get("sub")
    return str(subject) if subject is not None else None


def create_token_or_key_guard(security_state_getter: Callable[[], Tuple[bool, str | None]]):
    """Create a guard that accepts either a valid X-API-Key or a Bearer JWT token.

    This allows existing API-key based clients to continue working while supporting
    token-based auth for user-backed endpoints.
    """
    def guard(view_fn: Callable):
        @wraps(view_fn)
        def wrapped(*args, **kwargs):
            require_auth, api_key = security_state_getter()
            if not require_auth:
                return view_fn(*args, **kwargs)

            # First, allow X-API-Key if present and valid
            candidate = request.headers.get("X-API-Key", "").strip()
            if api_key and candidate == api_key:
                return view_fn(*args, **kwargs)

            # Next, try Authorization: Bearer <token>
            auth_hdr = request.headers.get("Authorization", "")
            if auth_hdr.startswith("Bearer "):
                token = auth_hdr.split(" ", 1)[1].strip()
                try:
                    payload = decode_access_token(token)
                    # expose subject to handlers via request context if needed
                    try:
                        from flask import g

                        g.token_subject = payload.get("sub")
                    except Exception:
                        pass
                    return view_fn(*args, **kwargs)
                except JWTError:
                    return jsonify({"error": "Invalid or expired token."}), 401

            return jsonify({"error": "Unauthorized. Missing valid X-API-Key or Bearer token."}), 401

        return wrapped

    return guard