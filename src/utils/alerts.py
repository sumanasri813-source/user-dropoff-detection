from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import yaml


THRESHOLDS_PATH = Path("mlops") / "ci_cd" / "quality_gates" / "thresholds.yaml"
ALERTS_PATH = Path("mlops") / "monitoring" / "alerts" / "alerts.jsonl"


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


def persist_alerts(alerts: List[Dict[str, Any]]) -> str | None:
    if not alerts:
        return None

    ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ALERTS_PATH.open("a", encoding="utf-8") as f:
        for alert in alerts:
            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **alert,
            }
            f.write(json.dumps(payload, ensure_ascii=True) + "\n")

    return str(ALERTS_PATH)
