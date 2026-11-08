"""
File Utilities — Temp directory management for analysis runs.
Each analysis gets a UUID-isolated directory that is cleaned up after use.
"""

import uuid
import shutil
from pathlib import Path

from app.config import settings


def create_run_directory() -> Path:
    """
    Creates a unique temp directory for a single analysis run.
    Returns the Path object.

    Example: /tmp/datapilot/3f2a1b4c-...../
    """
    run_id = str(uuid.uuid4())
    run_dir = Path(settings.temp_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def cleanup_run_directory(run_dir: Path) -> None:
    """
    Removes the temp directory for a completed analysis run.
    Safe to call even if the directory doesn't exist.
    Called on success, failure, and timeout.
    """
    try:
        shutil.rmtree(run_dir, ignore_errors=True)
    except Exception:
        pass  # Cleanup failure should never crash the app


def safe_csv_path(run_dir: Path) -> Path:
    """Returns the expected CSV input path inside a run directory."""
    return run_dir / "input.csv"
