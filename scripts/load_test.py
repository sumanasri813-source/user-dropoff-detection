#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import statistics
import threading
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List

import requests

DEFAULT_PAYLOAD = {
    "days_signup_age": 250,
    "recency_days": 45,
    "frequency_total": 9,
    "session_duration_avg": 6.5,
    "feature_count_used": 2,
    "device_type": "mobile",
    "os_type": "android",
    "user_segment": "free",
    "region": "north",
}


@dataclass
class Sample:
    endpoint: str
    status_code: int | None
    latency_ms: float
    error: str | None = None


@dataclass
class LoadTestSummary:
    base_url: str
    duration_seconds: int
    concurrency: int
    total_requests: int
    succeeded_requests: int
    failed_requests: int
    status_counts: Dict[str, int]
    endpoint_counts: Dict[str, int]
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    mean_latency_ms: float
    samples: List[Dict[str, Any]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a simple API load test against the user dropoff service."
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Base URL of the API under test",
    )
    parser.add_argument("--duration", type=int, default=300, help="Duration in seconds")
    parser.add_argument(
        "--concurrency", type=int, default=6, help="Number of worker threads"
    )
    parser.add_argument("--api-key", default="", help="Optional X-API-Key header value")
    parser.add_argument(
        "--predict-weight",
        type=int,
        default=8,
        help="Relative weight for /predict requests",
    )
    parser.add_argument(
        "--health-weight",
        type=int,
        default=3,
        help="Relative weight for /health requests",
    )
    parser.add_argument(
        "--batch-weight",
        type=int,
        default=1,
        help="Relative weight for /predict-batch requests",
    )
    parser.add_argument(
        "--output",
        default="results/load_test_summary.json",
        help="Where to write the JSON summary",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=25,
        help="How many request samples to keep in the summary",
    )
    return parser.parse_args()


def build_payload() -> Dict[str, Any]:
    payload = DEFAULT_PAYLOAD.copy()
    payload.update(
        {
            "days_signup_age": random.randint(30, 730),
            "recency_days": random.randint(1, 120),
            "frequency_total": random.randint(1, 30),
            "session_duration_avg": round(random.uniform(1.0, 30.0), 2),
            "feature_count_used": random.randint(1, 8),
            "device_type": random.choice(["mobile", "desktop", "tablet"]),
            "os_type": random.choice(["android", "ios", "windows", "linux", "macos"]),
            "user_segment": random.choice(["free", "pro", "enterprise"]),
            "region": random.choice(["north", "south", "east", "west"]),
        }
    )
    return payload


def make_batch_payload(size: int = 5) -> Dict[str, Any]:
    return {"records": [build_payload() for _ in range(size)]}


def choose_endpoint(weights: Dict[str, int]) -> str:
    population = list(weights.keys())
    values = list(weights.values())
    return random.choices(population, weights=values, k=1)[0]


def worker(
    stop_time: float,
    base_url: str,
    headers: Dict[str, str],
    weights: Dict[str, int],
    samples: List[Sample],
    samples_lock: threading.Lock,
    counters: Counter,
    latencies: List[float],
    latency_lock: threading.Lock,
) -> None:
    session = requests.Session()
    while time.time() < stop_time:
        endpoint = choose_endpoint(weights)
        url = f"{base_url}{endpoint}"
        payload = None
        method = "GET"
        if endpoint == "/predict":
            method = "POST"
            payload = build_payload()
        elif endpoint == "/predict-batch":
            method = "POST"
            payload = make_batch_payload()

        started = time.perf_counter()
        status_code: int | None = None
        error: str | None = None
        try:
            if method == "GET":
                response = session.get(url, headers=headers, timeout=10)
            else:
                response = session.post(url, json=payload, headers=headers, timeout=10)
            status_code = response.status_code
            response.raise_for_status()
        except Exception as exc:
            error = str(exc)
        finally:
            latency_ms = (time.perf_counter() - started) * 1000.0
            with latency_lock:
                latencies.append(latency_ms)
            with samples_lock:
                counters[endpoint] += 1
                if status_code is not None and 200 <= status_code < 400:
                    counters["success"] += 1
                else:
                    counters["failure"] += 1
                counters[
                    f"status_{status_code if status_code is not None else 'error'}"
                ] += 1
                samples.append(
                    Sample(
                        endpoint=endpoint,
                        status_code=status_code,
                        latency_ms=latency_ms,
                        error=error,
                    )
                )

        time.sleep(random.uniform(0.05, 0.25))


def percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    index = int(round((pct / 100.0) * (len(ordered) - 1)))
    return ordered[index]


def run_load_test(args: argparse.Namespace) -> LoadTestSummary:
    stop_time = time.time() + args.duration
    headers = {}
    if args.api_key:
        headers["X-API-Key"] = args.api_key

    weights = {
        "/health": args.health_weight,
        "/predict": args.predict_weight,
        "/predict-batch": args.batch_weight,
    }

    samples: List[Sample] = []
    samples_lock = threading.Lock()
    latencies: List[float] = []
    latency_lock = threading.Lock()
    counters: Counter = Counter()

    threads = [
        threading.Thread(
            target=worker,
            args=(
                stop_time,
                args.base_url.rstrip("/"),
                headers,
                weights,
                samples,
                samples_lock,
                counters,
                latencies,
                latency_lock,
            ),
            daemon=True,
        )
        for _ in range(args.concurrency)
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    sampled = samples[-args.sample_limit :]
    total_requests = counters["success"] + counters["failure"]
    summary = LoadTestSummary(
        base_url=args.base_url,
        duration_seconds=args.duration,
        concurrency=args.concurrency,
        total_requests=total_requests,
        succeeded_requests=counters["success"],
        failed_requests=counters["failure"],
        status_counts={
            key.removeprefix("status_"): value
            for key, value in counters.items()
            if key.startswith("status_")
        },
        endpoint_counts={
            key: value for key, value in counters.items() if key in weights
        },
        p50_latency_ms=round(percentile(latencies, 50), 2),
        p95_latency_ms=round(percentile(latencies, 95), 2),
        p99_latency_ms=round(percentile(latencies, 99), 2),
        mean_latency_ms=round(statistics.fmean(latencies) if latencies else 0.0, 2),
        samples=[asdict(sample) for sample in sampled],
    )
    return summary


def main() -> int:
    args = parse_args()
    print(
        f"Running load test against {args.base_url} for {args.duration}s with {args.concurrency} workers"
    )
    summary = run_load_test(args)
    print(json.dumps(asdict(summary), indent=2, sort_keys=True))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(asdict(summary), indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"Wrote load test summary to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
