from __future__ import annotations

import hashlib
import json
import tempfile
from collections import deque
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import yaml

try:
    import fcntl
except Exception:
    fcntl = None


THRESHOLDS_PATH = Path("mlops") / "ci_cd" / "quality_gates" / "thresholds.yaml"
ALERTS_PATH = Path("mlops") / "monitoring" / "alerts" / "alerts.jsonl"
ALERTS_LOCK_PATH = ALERTS_PATH.with_suffix(".lock")
ALERTS_RETENTION_DAYS = 30
ALERTS_MAX_RECORDS = 2000

# Alert dedup state: maps alert_type -> (hash, timestamp)
_last_persisted_alert: Dict[str, tuple[str, datetime]] = {}


def load_alert_thresholds() -> Dict[str, Any]:
    defaults: Dict[str, Any] = {
        "service": {
            "max_prediction_latency_ms": 300,
            "min_health_status": "healthy",
        }
    }

    if not THRESHOLDS_PATH.exists():
        return defaults

    with THRESHOLDS_PATH.open("r", encoding="utf-8") as f:
        payload = yaml.safe_load(f) or {}

    gates = payload.get("quality_gates", {}) if isinstance(payload, dict) else {}
    service_cfg = gates.get("service", {}) if isinstance(gates, dict) else {}

    merged = defaults.copy()
    merged["service"] = {
        "max_prediction_latency_ms": service_cfg.get(
            "max_prediction_latency_ms",
            defaults["service"]["max_prediction_latency_ms"],
        ),
        "min_health_status": service_cfg.get(
            "min_health_status", defaults["service"]["min_health_status"]
        ),
    }
    return merged


def _health_rank(value: str) -> int:
    mapping = {"healthy": 3, "degraded": 2, "unhealthy": 1}
    return mapping.get(str(value).lower(), 0)


@contextmanager
def _alerts_write_lock():
    if fcntl is None:
        yield
        return

    ALERTS_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ALERTS_LOCK_PATH.open("a", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _find_last_record_for_type(
    alert_type: str,
) -> tuple[Dict[str, Any] | None, datetime | None]:
    if not ALERTS_PATH.exists() or ALERTS_PATH.stat().st_size == 0:
        return None, None

    recent_lines: deque[str] = deque(maxlen=ALERTS_MAX_RECORDS)
    try:
        with ALERTS_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    recent_lines.append(line.strip())
    except Exception:
        return None, None

    for line in reversed(recent_lines):
        try:
            record = json.loads(line)
        except Exception:
            continue

        if record.get("type", "unknown") != alert_type:
            continue

        timestamp_raw = record.get("timestamp")
        if not timestamp_raw:
            return record, None

        try:
            record_time = datetime.fromisoformat(str(timestamp_raw))
        except Exception:
            return record, None

        if record_time.tzinfo is None:
            record_time = record_time.replace(tzinfo=timezone.utc)
        else:
            record_time = record_time.astimezone(timezone.utc)
        return record, record_time

    return None, None


def _compute_alert_hash(alert: Dict[str, Any]) -> str:
    """Compute a hash of alert content for dedup detection."""
    # Include type, metric, and value in hash to detect same alert state
    keys = ["type", "metric", "value", "threshold"]
    # Normalize numeric values to reduce noise from minor fluctuations
    normalized: Dict[str, Any] = {}
    for k in keys:
        v = alert.get(k)
        if isinstance(v, (int, float)):
            # Bucket latency metrics more coarsely to avoid jitter-driven churn
            metric_name = alert.get("metric", "")
            try:
                fv = float(v)
            except Exception:
                normalized[k] = v
                continue

            if isinstance(metric_name, str) and "latency" in metric_name:
                # Bucket latency into 200ms bins (increased from 100ms) to reduce jitter churn.
                normalized[k] = int(fv // 200.0) * 200
            else:
                # Round floats to 2 decimal places for other metrics
                normalized[k] = round(fv, 2)
        else:
            normalized[k] = v

    content = json.dumps(normalized, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(content.encode()).hexdigest()


def _should_persist_alert(alert: Dict[str, Any], throttle_minutes: int) -> bool:
    """
    Determine if an alert should be persisted based on dedup/throttle rules.

    Returns True if:
    - This is the first time seeing this alert type, OR
    - The alert content has changed (different hash), OR
    - The throttle window has expired (since last occurrence of this type)
    """
    alert_type = alert.get("type", "unknown")
    current_hash = _compute_alert_hash(alert)
    now = datetime.now(timezone.utc)

    if alert_type not in _last_persisted_alert:
        # First time seeing this alert type
        _last_persisted_alert[alert_type] = (current_hash, now)
        return True

    last_hash, last_time = _last_persisted_alert[alert_type]
    throttle_window = timedelta(minutes=throttle_minutes)

    if current_hash != last_hash:
        # Alert state changed (different metric values)
        _last_persisted_alert[alert_type] = (current_hash, now)
        return True

    if now - last_time >= throttle_window:
        # Throttle window expired; re-persist same alert
        _last_persisted_alert[alert_type] = (current_hash, now)
        return True

    # Duplicate within throttle window; skip
    return False


def _prune_alert_history() -> None:
    """Keep the alert JSONL store bounded by age and record count."""
    if not ALERTS_PATH.exists() or ALERTS_PATH.stat().st_size == 0:
        return

    try:
        with ALERTS_PATH.open("r", encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f if line.strip()]
    except Exception:
        return

    if not lines:
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=ALERTS_RETENTION_DAYS)
    retained: List[str] = []

    for line in lines:
        try:
            record = json.loads(line)
        except Exception:
            retained.append(line)
            continue

        timestamp_raw = record.get("timestamp")
        if not timestamp_raw:
            retained.append(line)
            continue

        try:
            record_time = datetime.fromisoformat(str(timestamp_raw))
        except Exception:
            retained.append(line)
            continue

        if record_time.tzinfo is None:
            record_time = record_time.replace(tzinfo=timezone.utc)
        else:
            record_time = record_time.astimezone(timezone.utc)

        if record_time >= cutoff:
            retained.append(line)

    if len(retained) > ALERTS_MAX_RECORDS:
        retained = retained[-ALERTS_MAX_RECORDS:]

    if len(retained) == len(lines):
        return

    ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_handle = None
    try:
        tmp_handle = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(ALERTS_PATH.parent),
            prefix=f"{ALERTS_PATH.stem}.",
            suffix=".tmp",
            delete=False,
        )
        with tmp_handle as f:
            for line in retained:
                f.write(line + "\n")
        Path(tmp_handle.name).replace(ALERTS_PATH)
    except Exception:
        if tmp_handle is not None:
            try:
                Path(tmp_handle.name).unlink(missing_ok=True)
            except Exception:
                pass


def evaluate_alert_rules(
    snapshot: Dict[str, Any], health_status: str
) -> List[Dict[str, Any]]:
    thresholds = load_alert_thresholds()
    service = thresholds.get("service", {})

    alerts: List[Dict[str, Any]] = []

    max_latency = float(service.get("max_prediction_latency_ms", 300))
    p95_latency = float(snapshot.get("latency", {}).get("p95_ms", 0.0))
    if p95_latency > max_latency:
        alerts.append(
            {
                "type": "service_latency",
                "severity": "warning",
                "message": f"p95 latency {p95_latency:.2f}ms exceeds threshold {max_latency:.2f}ms",
                "metric": "latency.p95_ms",
                "value": p95_latency,
                "threshold": max_latency,
            }
        )

    drift = snapshot.get("drift_stub", {})
    if drift.get("status") == "alert":
        alerts.append(
            {
                "type": "drift_stub",
                "severity": "warning",
                "message": "Prediction mean drift distance exceeded threshold",
                "metric": "drift_stub.distance",
                "value": drift.get("distance"),
                "threshold": drift.get("threshold"),
            }
        )

    min_health = str(service.get("min_health_status", "healthy"))
    if _health_rank(health_status) < _health_rank(min_health):
        alerts.append(
            {
                "type": "health_status",
                "severity": "critical",
                "message": f"Health status '{health_status}' below minimum '{min_health}'",
                "metric": "health.status",
                "value": health_status,
                "threshold": min_health,
            }
        )

    return alerts


def persist_alerts(
    alerts: List[Dict[str, Any]], throttle_minutes: int = 15
) -> str | None:
    """
    Persist alerts to JSONL file with dedup/throttle logic.

    Args:
        alerts: list of alert dicts
        throttle_minutes: minutes to throttle repeated identical alerts (default: 15)

    Returns:
        path to alerts file if any alerts persisted, None otherwise
    """
    if not alerts:
        return None

    with _alerts_write_lock():
        alerts_to_persist = [
            alert for alert in alerts if _should_persist_alert(alert, throttle_minutes)
        ]

        try:
            filtered: List[Dict[str, Any]] = []
            for alert in alerts_to_persist:
                alert_type = alert.get("type", "unknown")
                last_record, last_time = _find_last_record_for_type(alert_type)
                if last_record is None:
                    filtered.append(alert)
                    continue

                try:
                    current_hash = _compute_alert_hash(alert)
                    last_hash = _compute_alert_hash(last_record)
                except Exception:
                    filtered.append(alert)
                    continue

                if last_time is not None and current_hash == last_hash:
                    throttle_window = timedelta(minutes=throttle_minutes)
                    if datetime.now(timezone.utc) - last_time < throttle_window:
                        continue

                filtered.append(alert)

            alerts_to_persist = filtered
        except Exception:
            pass

        if not alerts_to_persist:
            return None

        ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with ALERTS_PATH.open("a", encoding="utf-8") as f:
            for alert in alerts_to_persist:
                payload = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **alert,
                }
                f.write(json.dumps(payload, ensure_ascii=True) + "\n")

        try:
            _prune_alert_history()
        except Exception:
            pass

        return str(ALERTS_PATH)
