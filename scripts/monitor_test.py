#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import time


def _debug_enabled() -> bool:
    return os.getenv("MONITOR_TEST_DEBUG", "0").lower() in {"1", "true", "yes", "on"}


def main() -> int:
    if _debug_enabled():
        print(f"[DEBUG] Python version: {sys.version}")
        print(f"[DEBUG] Python executable: {sys.executable}")
        print(f"[DEBUG] Initial sys.path: {sys.path[:3]}")

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if root not in sys.path:
        sys.path.insert(0, root)
        if _debug_enabled():
            print(f"[DEBUG] Added project root to sys.path: {root}")

    if sys.version_info < (3, 7):
        print("ERROR: this script requires Python 3.7+; run with `python3 scripts/monitor_test.py`.")
        return 1

    from src.api import app as api_app

    print("Running 3 monitoring cycles...")
    for i in range(3):
        print(f"Cycle {i + 1}")
        api_app.run_monitoring_cycle()
        time.sleep(1)
    print("Done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
