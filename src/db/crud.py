from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from src.db.models import PredictionRecord, UserProfile
from src.utils.auth import hash_password
from src.db.models import RefreshToken
from datetime import timedelta
import uuid
from sqlalchemy import and_
from src.db.models import AuditLog
from datetime import datetime, timezone
import json


def _user_to_dict(user: UserProfile) -> Dict[str, Any]:
    return {
        "id": user.id,
        "external_user_id": user.external_user_id,
        "roles": user.roles,
        "email": user.email,
        "user_segment": user.user_segment,
        "device_type": user.device_type,
        "os_type": user.os_type,
        "region": user.region,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


def _prediction_to_dict(prediction: PredictionRecord) -> Dict[str, Any]:
    return {
        "id": prediction.id,
        "user_id": prediction.user_id,
        "request_id": prediction.request_id,
        "dropoff_probability": prediction.dropoff_probability,
        "predicted_label": prediction.predicted_label,
        "risk_level": prediction.risk_level,
        "threshold_used": prediction.threshold_used,
        "payload_json": prediction.payload_json,
        "created_at": prediction.created_at.isoformat() if prediction.created_at else None,
    }


def create_user(session: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
    user = UserProfile(
        external_user_id=str(payload["external_user_id"]),
        email=payload.get("email"),
        user_segment=payload.get("user_segment"),
        device_type=payload.get("device_type"),
        os_type=payload.get("os_type"),
        region=payload.get("region"),
    )
    # optional roles
    if payload.get("roles"):
        user.roles = str(payload.get("roles"))
    # Optional password handling: if provided, store hashed password
    if payload.get("password"):
        user.password_hash = hash_password(str(payload.get("password")))
    session.add(user)
    session.commit()
    session.refresh(user)
    return _user_to_dict(user)


def list_users(
    session: Session,
    limit: int = 100,
    offset: int = 0,
    user_segment: str | None = None,
) -> List[Dict[str, Any]]:
    """List users with optimized filtering. O(log n + k) with index on user_segment and id."""
    query = session.query(UserProfile)
    if user_segment:
        query = query.filter(UserProfile.user_segment == str(user_segment))

    # Index-based sorting on primary key for stable pagination
    rows = query.order_by(UserProfile.id.desc()).offset(offset).limit(limit).all()
    return [_user_to_dict(row) for row in rows]


def get_user(session: Session, user_id: int) -> Dict[str, Any] | None:
    user = session.query(UserProfile).filter(UserProfile.id == user_id).first()
    return _user_to_dict(user) if user else None


def update_user(session: Session, user_id: int, payload: Dict[str, Any]) -> Dict[str, Any] | None:
    user = session.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user:
        return None

    for key in ["email", "user_segment", "device_type", "os_type", "region"]:
        if key in payload:
            setattr(user, key, payload.get(key))

    if "external_user_id" in payload:
        user.external_user_id = str(payload["external_user_id"])

    user.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(user)
    return _user_to_dict(user)


def delete_user(session: Session, user_id: int) -> bool:
    user = session.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user:
        return False

    session.delete(user)
    session.commit()
    return True


def create_prediction_record(
    session: Session,
    prediction_result: Dict[str, Any],
    request_id: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    user_id = None
    external_user_id = payload.get("external_user_id")
    if external_user_id:
        user = session.query(UserProfile).filter(UserProfile.external_user_id == str(external_user_id)).first()
        if user:
            user_id = user.id

    record = PredictionRecord(
        user_id=user_id,
        request_id=request_id,
        dropoff_probability=float(prediction_result.get("dropoff_probability", 0.0)),
        predicted_label=int(prediction_result.get("predicted_label", 0)),
        risk_level=str(prediction_result.get("risk_level", "unknown")),
        threshold_used=float(prediction_result.get("threshold_used", 0.5)),
        payload_json=json.dumps(payload, ensure_ascii=True),
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return _prediction_to_dict(record)


def create_refresh_token_record(session: Session, user_id: int, jti: str, expires_at) -> Dict[str, Any]:
    token = RefreshToken(user_id=user_id, jti=jti, expires_at=expires_at)
    session.add(token)
    session.commit()
    session.refresh(token)
    return {"id": token.id, "jti": token.jti, "user_id": token.user_id, "expires_at": token.expires_at.isoformat() if token.expires_at else None}


def get_refresh_token_record(session: Session, jti: str) -> RefreshToken | None:
    return session.query(RefreshToken).filter(RefreshToken.jti == str(jti)).first()


def revoke_refresh_token(session: Session, jti: str) -> bool:
    token = session.query(RefreshToken).filter(RefreshToken.jti == str(jti)).first()
    if not token:
        return False
    token.revoked = True
    session.commit()
    return True


def log_audit_event(
    session: Session,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: int | None = None,
    old_values: dict | None = None,
    new_values: dict | None = None,
    changes_summary: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    reason: str | None = None,
) -> Dict[str, Any]:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        old_values=json.dumps(old_values) if old_values is not None else None,
        new_values=json.dumps(new_values) if new_values is not None else None,
        changes_summary=changes_summary,
        ip_address=ip_address,
        user_agent=user_agent,
        reason=reason,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return {"id": entry.id, "user_id": entry.user_id, "action": entry.action, "resource_type": entry.resource_type}


def cleanup_expired_refresh_tokens(session: Session) -> int:
    """Remove expired refresh token records and return count removed."""
    now = datetime.now(timezone.utc)
    expired = session.query(RefreshToken).filter(RefreshToken.expires_at != None).filter(RefreshToken.expires_at < now).all()
    count = 0
    for token in expired:
        session.delete(token)
        count += 1
    session.commit()
    return count


def get_audit_logs(
    session: Session,
    limit: int = 50,
    offset: int = 0,
    user_id: int | None = None,
    action: str | None = None,
    resource_type: str | None = None,
) -> Dict[str, Any]:
    """Return paginated audit logs with optional filtering by user_id, action, and resource_type."""
    query = session.query(AuditLog)
    if user_id is not None:
        query = query.filter(AuditLog.user_id == int(user_id))
    if action:
        query = query.filter(AuditLog.action == str(action))
    if resource_type:
        query = query.filter(AuditLog.resource_type == str(resource_type))

    query = query.order_by(AuditLog.id.desc())
    total = query.count()
    rows = query.offset(offset).limit(limit).all()
    results = []
    for r in rows:
        results.append({
            "id": r.id,
            "user_id": r.user_id,
            "action": r.action,
            "resource_type": r.resource_type,
            "resource_id": r.resource_id,
            "changes_summary": r.changes_summary,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return {"total": total, "logs": results}


def cleanup_old_audit_logs(session: Session, retention_days: int = 90) -> int:
    """Delete audit log entries older than retention_days and return count removed."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=int(retention_days))
    old = session.query(AuditLog).filter(AuditLog.created_at != None).filter(AuditLog.created_at < cutoff).all()
    count = 0
    for entry in old:
        session.delete(entry)
        count += 1
    session.commit()
    return count


def delete_audit_log(session: Session, log_id: int) -> bool:
    entry = session.query(AuditLog).filter(AuditLog.id == int(log_id)).first()
    if not entry:
        return False
    session.delete(entry)
    session.commit()
    return True


def list_predictions(
    session: Session,
    limit: int = 100,
    offset: int = 0,
    risk_level: str | None = None,
    min_probability: float | None = None,
) -> List[Dict[str, Any]]:
    """List predictions with optimized filtering. O(log n + k) with indexes on risk_level, created_at, and dropoff_probability."""
    query = session.query(PredictionRecord)
    if risk_level:
        query = query.filter(PredictionRecord.risk_level == str(risk_level))
    if min_probability is not None:
        query = query.filter(PredictionRecord.dropoff_probability >= float(min_probability))

    # Index-based sorting on primary key for stable pagination - O(log n)
    rows = query.order_by(PredictionRecord.id.desc()).offset(offset).limit(limit).all()
    return [_prediction_to_dict(row) for row in rows]
