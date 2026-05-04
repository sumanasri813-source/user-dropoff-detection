"""Environment validator for application startup.

This module exposes `validate_env` which checks for required environment
variables and exits with a non-zero code when any required variable is
missing. It is safe to import and call from the app's startup logic.
"""
from __future__ import annotations

import os
import sys
from typing import Iterable, List


def validate_env(required: Iterable[str] | None = None, fail_on_missing: bool = True) -> List[str]:
    """Validate that required environment variables are present.

    Args:
        required: Iterable of environment variable names to check. If None,
            defaults to a conservative set used by the app.
        fail_on_missing: If True, call `sys.exit(1)` when missing vars are found.

    Returns:
        List of missing environment variable names.
    """
    if required is None:
        required = ["SESSION_SECRET_KEY", "JWT_SECRET_KEY"]

    missing = [name for name in required if not os.getenv(name)]
    if missing:
        msg = f"Missing required environment variables: {', '.join(missing)}"
        print(msg, file=sys.stderr)
        if fail_on_missing:
            sys.exit(1)
    return missing


if __name__ == "__main__":
    # CLI usage: exit nonzero if any required env vars are missing
    validate_env()
