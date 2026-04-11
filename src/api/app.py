from __future__ import annotations

import atexit
import time
import uuid
from typing import Any, Dict, Tuple

from flask import Flask, g, jsonify, request

from src.api.prediction_service import (
    load_decision_threshold,
    load_model,
    load_risk_levels,
    predict_batch,
    predict_one,
    validate_payload,
)
from src.utils.alerts import evaluate_alert_rules, persist_alerts
from src.utils.health import HealthChecker
from src.utils.logger import get_logger
from src.utils.metrics import get_collector, request_id_var
from src.utils.monitoring_worker import BackgroundMonitorWorker


app = Flask(__name__)
logger = get_logger("api")
collector = get_collector()

model: Any = None
threshold: float = 0.5
risk_levels: Dict[str, float] = {"high": 0.7, "medium": 0.4, "low": 0.0}
monitor_worker: BackgroundMonitorWorker | None = None


def _load_api_config() -> Tuple[str, int, bool]:
    host = "0.0.0.0"
    port = 5000
    debug = False
    try:
        from src.utils.config_loader import load_config

        cfg = load_config("config.yaml")
        api_cfg = cfg.get("deployment", {}).get("api", {})
        host = str(api_cfg.get("host", host))
        port = int(api_cfg.get("port", port))
        debug = bool(api_cfg.get("debug", debug))
    except Exception:
        pass
    return host, port, debug


def _load_model_path() -> str:
    model_path = "models/final_model.pkl"
    try:
        from src.utils.config_loader import load_config

        cfg = load_config("config.yaml")
        model_path = str(cfg.get("deployment", {}).get("model_path", model_path))
    except Exception:
        pass
    return model_path


def run_monitoring_cycle() -> None:
    persisted = collector.maybe_persist(force=False)
    if persisted:
        logger.info("metrics_persisted", **persisted)

    health_status = HealthChecker.run_full_check().status
    alerts = evaluate_alert_rules(collector.get_api_snapshot(), health_status=health_status)
    alert_path = persist_alerts(alerts)
    if alert_path and alerts:
        logger.warning("alerts_triggered", alert_count=len(alerts), alert_path=alert_path)


def start_monitoring_worker(interval_seconds: float = 30.0) -> None:
    global monitor_worker
    if monitor_worker and monitor_worker.is_running():
        return

    monitor_worker = BackgroundMonitorWorker(cycle_fn=run_monitoring_cycle, interval_seconds=interval_seconds)
    monitor_worker.start()


def stop_monitoring_worker() -> None:
    global monitor_worker
    if monitor_worker and monitor_worker.is_running():
        monitor_worker.stop(timeout_seconds=5.0)


atexit.register(stop_monitoring_worker)


@app.before_request
def before_request_hooks() -> None:
    global model, threshold, risk_levels

    g.request_start = time.perf_counter()
    g.request_id = str(uuid.uuid4())
    request_id_var.set(g.request_id)

    if model is None:
        model = load_model(_load_model_path())
        threshold = load_decision_threshold()
        risk_levels = load_risk_levels()

    collector.increment_counter("api_requests_total")
    collector.increment_counter(f"api_requests_{request.method}_{request.path}")


@app.after_request
def after_request_hooks(response):
    start = getattr(g, "request_start", None)
    latency_ms = 0.0
    if start is not None:
        latency_ms = (time.perf_counter() - start) * 1000.0
        collector.record_latency(latency_ms=latency_ms, endpoint=request.path)

    status_group = f"api_status_{response.status_code // 100}xx"
    collector.increment_counter(status_group)

    logger.info(
        "request_completed",
        request_id=getattr(g, "request_id", ""),
        method=request.method,
        path=request.path,
        status_code=response.status_code,
        latency_ms=round(latency_ms, 3),
    )

    try:
        run_monitoring_cycle()
    except Exception as monitor_exc:
        logger.error("monitoring_hook_failed", error=str(monitor_exc))

    return response


@app.errorhandler(Exception)
def handle_exception(exc: Exception):
    collector.increment_counter("api_unhandled_exceptions")
    logger.error(
        "unhandled_exception",
        request_id=getattr(g, "request_id", ""),
        path=request.path if request else "",
        error=str(exc),
    )
    return jsonify({"error": "Internal server error", "request_id": getattr(g, "request_id", "")}), 500


@app.route("/favicon.ico", methods=["GET"])
def favicon() -> tuple:
    return ("", 204)


@app.route("/health", methods=["GET"])
def health() -> tuple:
    health_status = HealthChecker.run_full_check()
    health_payload = HealthChecker.health_to_dict(health_status)
    monitor_snapshot = collector.get_api_snapshot()

    response = {
        "status": "ok" if health_payload.get("status") != "unhealthy" else "error",
        "model_loaded": model is not None,
        "threshold": threshold,
        "health": health_payload,
        "monitoring": monitor_snapshot,
        "worker": {
            "running": bool(monitor_worker and monitor_worker.is_running()),
        },
    }

    logger.info("health_checked", health_status=health_payload.get("status"), model_loaded=model is not None)
    return jsonify(response), (200 if health_payload.get("status") != "unhealthy" else 503)


@app.route("/monitor", methods=["GET"])
def monitor() -> tuple:
    return jsonify(collector.get_api_snapshot()), 200


@app.route("/monitor/persist", methods=["POST"])
def monitor_persist() -> tuple:
    persisted = collector.maybe_persist(force=True)
    return jsonify({"persisted": bool(persisted), "paths": persisted or {}}), 200


@app.route("/predict", methods=["POST"])
def predict() -> tuple:
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    ok, message = validate_payload(payload)
    if not ok:
        collector.increment_counter("prediction_validation_errors")
        return jsonify({"error": message, "request_id": getattr(g, "request_id", "")}), 400

    try:
        result = predict_one(model, payload, threshold, risk_levels)
        return jsonify({**result, "request_id": getattr(g, "request_id", "")}), 200
    except Exception as exc:
        collector.increment_counter("prediction_runtime_errors")
        logger.error("predict_failed", request_id=getattr(g, "request_id", ""), error=str(exc))
        return jsonify({"error": str(exc), "request_id": getattr(g, "request_id", "")}), 400


@app.route("/predict-batch", methods=["POST"])
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
    host, port, debug = _load_api_config()
    start_monitoring_worker(interval_seconds=30.0)
    logger.info("api_starting", host=host, port=port, debug=debug)
    app.run(host=host, port=port, debug=debug)
