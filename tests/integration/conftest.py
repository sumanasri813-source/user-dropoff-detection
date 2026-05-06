from __future__ import annotations

import os
import subprocess
import sys
import time
from contextlib import suppress
from pathlib import Path
from typing import Iterator
from urllib.error import URLError
from urllib.request import urlopen

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
API_HEALTH_URL = os.getenv("INTEGRATION_API_HEALTH_URL", "http://127.0.0.1:8000/health")
GATEWAY_HEALTH_URL = os.getenv("GATEWAY_HEALTH_URL", "http://127.0.0.1:8080/health")


def _is_healthy(url: str) -> bool:
    try:
        with urlopen(url, timeout=1) as response:
            return 200 <= getattr(response, "status", 200) < 300
    except Exception:
        return False


def _wait_for_health(url: str, timeout_seconds: int = 60) -> None:
    deadline = time.time() + timeout_seconds
    last_error = None
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=2) as response:
                if 200 <= getattr(response, "status", 200) < 300:
                    return
        except Exception as exc:
            last_error = exc
        time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


def _start_api_server() -> subprocess.Popen[str]:
    env = os.environ.copy()
    env.setdefault("SESSION_SECRET_KEY", "test-session-secret-key-for-integration")
    env.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-for-integration")
    env.setdefault("FLASK_ENV", "development")
    env.setdefault("API_HOST", "0.0.0.0")
    env.setdefault("API_PORT", "8000")

    log_path = REPO_ROOT / "logs" / "integration-api.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("a", encoding="utf-8")
    return subprocess.Popen(
        [sys.executable, "-m", "src.api.app"],
        cwd=REPO_ROOT,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        text=True,
    )


def _start_gateway_server() -> subprocess.Popen[str]:
    env = os.environ.copy()
    env.setdefault("PORT", "8080")
    env.setdefault("PYTHON_MODEL_SERVICE_URL", "http://127.0.0.1:8000/predict")
    env.setdefault("MODEL_NAME", "dropoff_classifier")
    env.setdefault("MODEL_VERSION", "v1")

    gateway_dir = REPO_ROOT / "gateway" / "node-minimal"
    log_path = REPO_ROOT / "logs" / "integration-gateway.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("a", encoding="utf-8")
    return subprocess.Popen(
        ["node", "server.js"],
        cwd=gateway_dir,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        text=True,
    )


@pytest.fixture(scope="session", autouse=True)
def ensure_gateway_stack() -> Iterator[None]:
    api_proc = None
    gateway_proc = None

    if not _is_healthy(API_HEALTH_URL):
        api_proc = _start_api_server()
        _wait_for_health(API_HEALTH_URL)

    if not _is_healthy(GATEWAY_HEALTH_URL):
        gateway_proc = _start_gateway_server()
        _wait_for_health(GATEWAY_HEALTH_URL)

    try:
        yield
    finally:
        for proc in (gateway_proc, api_proc):
            if proc is None:
                continue
            with suppress(Exception):
                proc.terminate()
            with suppress(Exception):
                proc.wait(timeout=10)
            with suppress(Exception):
                if proc.poll() is None:
                    proc.kill()
