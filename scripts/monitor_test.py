#!/usr/bin/env python3
import time
import sys
import os

# Debug: Print Python version and sys.path for troubleshooting
print(f"[DEBUG] Python version: {sys.version}")
print(f"[DEBUG] Python executable: {sys.executable}")
print(f"[DEBUG] Initial sys.path: {sys.path[:3]}")  # Show first 3 entries

# Ensure project root is on sys.path so `src` imports work
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
    print(f"[DEBUG] Added project root to sys.path: {ROOT}")

# Guard against running under Python 2 or very old Python 3 interpreters.
if sys.version_info < (3, 7):
    print("ERROR: this script requires Python 3.7+; run with `python3 scripts/monitor_test.py`.")
    sys.exit(1)

# Run a few monitoring cycles to observe logging and alerts persistence
from src.api import app as api_app

print('Running 3 monitoring cycles...')
for i in range(3):
    print(f'Cycle {i+1}')
    api_app.run_monitoring_cycle()
    time.sleep(1)
print('Done')
