from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List
import os

import yaml


THRESHOLDS_PATH = Path("mlops") / "ci_cd" / "quality_gates" / "thresholds.yaml"
ALERTS_PATH = Path("mlops") / "monitoring" / "alerts" / "alerts.jsonl"
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
        "max_prediction_latency_ms": service_cfg.get("max_prediction_latency_ms", defaults["service"]["max_prediction_latency_ms"]),
        "min_health_status": service_cfg.get("min_health_status", defaults["service"]["min_health_status"]),
    }
    return merged


def _health_rank(value: str) -> int:
    mapping = {"healthy": 3, "degraded": 2, "unhealthy": 1}
    return mapping.get(str(value).lower(), 0)


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
                # Bucket latency into 100ms bins, rounded down to reduce jitter churn.
                normalized[k] = int(fv // 100.0) * 100
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
            timestamp_raw = record.get("timestamp")
            if timestamp_raw:
                record_time = datetime.fromisoformat(str(timestamp_raw))
                if record_time.tzinfo is None:
                    record_time = record_time.replace(tzinfo=timezone.utc)
                else:
                    record_time = record_time.astimezone(timezone.utc)
                if record_time >= cutoff:
                    retained.append(line)
                continue
        except Exception:
            # Keep malformed lines rather than dropping potentially useful history.
            retained.append(line)

    if len(retained) > ALERTS_MAX_RECORDS:
        retained = retained[-ALERTS_MAX_RECORDS:]

    if len(retained) == len(lines):
        return

    tmp_path = ALERTS_PATH.with_suffix(".jsonl.tmp")
    ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with tmp_path.open("w", encoding="utf-8") as f:
        for line in retained:
            f.write(line + "\n")
    tmp_path.replace(ALERTS_PATH)


def evaluate_alert_rules(snapshot: Dict[str, Any], health_status: str) -> List[Dict[str, Any]]:
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


def persist_alerts(alerts: List[Dict[str, Any]], throttle_minutes: int = 10) -> str | None:
    """
    Persist alerts to JSONL file with dedup/throttle logic.
    
    Args:
        alerts: list of alert dicts
        throttle_minutes: minutes to throttle repeated identical alerts (default: 10)
    
    Returns:
        path to alerts file if any alerts persisted, None otherwise
    """
    if not alerts:
        return None

    # Filter alerts through dedup logic (in-process)
    alerts_to_persist = [alert for alert in alerts if _should_persist_alert(alert, throttle_minutes)]

    # Cross-process dedup: check the last persisted alert on disk and skip
    # persisting if the same alert (by computed hash) was written within the
    # throttle window by another process.
    try:
        if ALERTS_PATH.exists() and ALERTS_PATH.stat().st_size > 0:
            last_line = None
            with ALERTS_PATH.open("r", encoding="utf-8") as f:
                for line in reversed(f.readlines()):
                    if line.strip():
                        last_line = line.strip()
                        break

            if last_line:
                last_record = json.loads(last_line)
                last_type = last_record.get("type", "unknown")
                last_hash = _compute_alert_hash(last_record)
                last_time = None
                try:
                    last_time = datetime.fromisoformat(last_record.get("timestamp"))
                except Exception:
                    last_time = None

                throttle_window = timedelta(minutes=throttle_minutes)
                now = datetime.now(timezone.utc)

                filtered = []
                for alert in alerts_to_persist:
                    try:
                        ahash = _compute_alert_hash(alert)
                        atype = alert.get("type", "unknown")
                    except Exception:
                        filtered.append(alert)
                        continue

                    # If last persisted record matches this alert and is within
                    # throttle window, skip it (cross-process dedup)
                    if last_time is not None and atype == last_type and ahash == last_hash and (now - last_time) < throttle_window:
                        continue

                    filtered.append(alert)

                alerts_to_persist = filtered
    except Exception:
        # If cross-process check fails for any reason, fall back to in-process logic
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

    _prune_alert_history()

    return str(ALERTS_PATH)
