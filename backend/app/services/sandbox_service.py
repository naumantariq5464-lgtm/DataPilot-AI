"""
Sandbox Service — Docker-based isolated Python execution.
Phase 5 — Complete Implementation.

Every analysis runs in a fresh container with strict resource limits.
AI-generated code NEVER runs inside the FastAPI process.
"""

import asyncio
import json
import shutil
import platform
from pathlib import Path

import docker
import docker.errors

from app.config import settings
from app.utils.file_utils import create_run_directory, cleanup_run_directory

# ── Concurrency limiter ───────────────────────────────────────────────────────
_semaphore = asyncio.Semaphore(settings.sandbox_max_concurrent)

# ── Docker client ─────────────────────────────────────────────────────────────
try:
    _docker_client = docker.from_env()
except Exception:
    _docker_client = None


def _to_docker_path(path: str) -> str:
    """
    Convert a host path to a Docker-mountable path.
    On Windows: C:\\path\\to\\dir  →  /c/path/to/dir
    On Linux/Mac: path is already correct.
    """
    if platform.system() == "Windows":
        import os
        path = os.path.abspath(path)
        drive, rest = os.path.splitdrive(path)
        drive_letter = drive.rstrip(":").lower()
        rest_forward = rest.replace("\\", "/")
        return f"/{drive_letter}{rest_forward}"
    return path


async def execute_in_sandbox(code: str, csv_path: str) -> dict:
    """
    Runs AI-generated Python code inside an isolated Docker container.
    Returns parsed JSON output from container stdout.
    """
    if _docker_client is None:
        return _error_result(
            "Docker is not available on this system. "
            "Ensure Docker is installed and the daemon is running.",
            error_type="docker_unavailable",
        )

    async with _semaphore:
        return await _run_container(code, csv_path)


async def _run_container(code: str, csv_path: str) -> dict:
    run_dir = create_run_directory()
    try:
        # Write analysis code
        code_dir = run_dir / "code"
        code_dir.mkdir()
        (code_dir / "analysis.py").write_text(code, encoding="utf-8")

        # Copy CSV
        csv_src = Path(csv_path)
        if not csv_src.exists():
            return _error_result(
                "CSV file not found for this dataset. Try re-uploading your file.",
                error_type="file_not_found",
            )

        data_dir = run_dir / "data"
        data_dir.mkdir()
        shutil.copy2(csv_src, data_dir / "input.csv")

        # Run in thread (docker SDK is sync)
        result = await asyncio.to_thread(
            _run_docker_container,
            str(code_dir),
            str(data_dir),
        )
        return result

    except Exception as e:
        return _error_result(
            f"Sandbox setup failed: {type(e).__name__}: {str(e)}",
            error_type="setup_error",
        )
    finally:
        cleanup_run_directory(run_dir)


def _run_docker_container(code_dir: str, data_dir: str) -> dict:
    """Synchronous Docker execution — called via asyncio.to_thread."""
    docker_code_dir = _to_docker_path(code_dir)
    docker_data_dir = _to_docker_path(data_dir)

    try:
        container = _docker_client.containers.run(
            image=settings.sandbox_image,
            volumes={
                docker_code_dir: {"bind": "/code", "mode": "ro"},
                docker_data_dir: {"bind": "/data", "mode": "ro"},
            },
            network_mode="none",
            nano_cpus=int(settings.sandbox_cpu_limit * 1e9),
            mem_limit=settings.sandbox_memory_limit,
            pids_limit=settings.sandbox_pids_limit,
            detach=True,
            stdout=True,
            stderr=True,
        )

        # Wait with timeout
        try:
            result = container.wait(timeout=settings.sandbox_timeout_seconds)
            exit_code = result.get("StatusCode", 1)
        except Exception:
            # Capture partial output before killing
            stdout_partial = ""
            try:
                stdout_partial = container.logs(
                    stdout=True, stderr=False
                ).decode("utf-8", errors="replace")[:500]
            except Exception:
                pass
            try:
                container.kill()
                container.remove(force=True)
            except Exception:
                pass
            return _error_result(
                f"Execution timed out after {settings.sandbox_timeout_seconds}s. "
                "Try a simpler or more focused analysis request.",
                error_type="timeout",
                stdout_preview=stdout_partial,
            )

        # Collect output
        stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
        stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")

        # Always log for backend debugging
        if stdout.strip():
            print(f"[Sandbox stdout]: {stdout[:800]}")
        if stderr.strip():
            print(f"[Sandbox stderr]: {stderr[:800]}")

        # Cleanup
        try:
            container.remove(force=True)
        except Exception:
            pass

        if exit_code != 0:
            return _extract_error(exit_code, stdout, stderr)

        return _parse_output(stdout)

    except docker.errors.ImageNotFound:
        return _error_result(
            f"Sandbox image '{settings.sandbox_image}' not found. "
            "Build it with: docker build -t datapilot-sandbox:latest backend/sandbox/",
            error_type="image_not_found",
        )
    except docker.errors.APIError as e:
        return _error_result(
            f"Docker API error: {str(e)[:300]}",
            error_type="docker_api_error",
        )
    except Exception as e:
        return _error_result(
            f"Unexpected sandbox error: {type(e).__name__}: {str(e)[:300]}",
            error_type="unexpected_error",
        )


def _extract_error(exit_code: int, stdout: str, stderr: str) -> dict:
    """
    Build a diagnostic error message when the container exits non-zero.
    Checks stderr first, then stdout for Python tracebacks.
    """
    # Prefer stderr
    error_detail = stderr.strip()

    # If stderr empty, look for Python traceback in stdout
    if not error_detail and stdout.strip():
        lines = stdout.strip().splitlines()
        tb_start = -1
        for i, line in enumerate(lines):
            stripped = line.strip()
            if (
                stripped.startswith("Traceback")
                or stripped.startswith("Error:")
                or stripped.startswith("Exception:")
                or (": " in stripped and any(
                    stripped.startswith(e)
                    for e in ("AttributeError", "ValueError", "TypeError",
                              "KeyError", "IndexError", "NameError",
                              "ImportError", "SyntaxError", "ZeroDivisionError",
                              "RuntimeError", "OverflowError", "MemoryError")
                ))
            ):
                tb_start = i
                break
        if tb_start >= 0:
            error_detail = "\n".join(lines[tb_start:])[:800]
        else:
            error_detail = stdout.strip()[:800]

    if not error_detail:
        error_detail = "No error output captured. The process may have crashed silently."

    return _error_result(
        f"Code execution failed (exit {exit_code}):\n{error_detail}",
        error_type="execution_error",
        exit_code=exit_code,
        stdout_preview=stdout.strip()[:300] if stdout.strip() else "",
    )


def _parse_output(stdout: str) -> dict:
    """
    Parse JSON from sandbox stdout.
    The runner prints a single JSON line — we scan from the bottom
    to skip any debug prints the AI code may have added.
    """
    if not stdout.strip():
        return _error_result(
            "Sandbox produced no output. The analysis code may have run "
            "without assigning the RESULT variable.",
            error_type="no_output",
        )

    # Scan all lines for valid JSON objects (most likely the last one)
    for line in reversed(stdout.strip().splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
            if not isinstance(data, dict):
                continue
            return {
                "success":    data.get("success", True),
                "insights":   data.get("insights", ""),
                "statistics": _sanitize_statistics(data.get("statistics", {})),
                "charts":     data.get("charts", []),
                "error":      data.get("error"),
            }
        except json.JSONDecodeError:
            continue

    return _error_result(
        f"Could not parse analysis output. "
        f"Output preview: {stdout.strip()[:300]}",
        error_type="parse_error",
    )


def _sanitize_statistics(stats: dict) -> dict:
    """
    Ensure all statistics values are JSON-safe and frontend-renderable.
    Converts any numpy types, arrays or objects to strings/numbers.
    """
    if not isinstance(stats, dict):
        return {}

    cleaned = {}
    for key, val in stats.items():
        if val is None:
            cleaned[key] = "N/A"
        elif isinstance(val, bool):
            cleaned[key] = str(val)
        elif isinstance(val, (int, float)):
            # Guard against NaN / Infinity which break JSON
            import math
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                cleaned[key] = "N/A"
            else:
                cleaned[key] = val
        elif isinstance(val, str):
            cleaned[key] = val
        elif isinstance(val, list):
            # Convert list to readable string
            cleaned[key] = _list_to_string(val)
        elif isinstance(val, dict):
            # Convert nested dict to key: value string
            cleaned[key] = " | ".join(f"{k}: {v}" for k, v in val.items())
        else:
            # numpy types, etc.
            try:
                import numpy as np  # noqa: F401
                if hasattr(val, 'item'):
                    cleaned[key] = val.item()  # numpy scalar → python scalar
                else:
                    cleaned[key] = str(val)
            except Exception:
                cleaned[key] = str(val)

    return cleaned


def _list_to_string(lst: list) -> str:
    """Convert a list to a human-readable string for display in statistics."""
    if not lst:
        return ""

    # Check if list of dicts with name/value keys (ranking format)
    if isinstance(lst[0], dict):
        parts = []
        for i, item in enumerate(lst):
            if isinstance(item, dict):
                name = item.get("name") or item.get("label") or item.get("category") or str(list(item.values())[0] if item else "")
                value = item.get("value") or item.get("count") or item.get("score") or (list(item.values())[1] if len(item) > 1 else "")
                parts.append(f"{i+1}. {name} — {value}")
            else:
                parts.append(f"{i+1}. {item}")
        return " | ".join(parts)

    # Simple list of primitives
    return " | ".join(str(x) for x in lst)


def _error_result(message: str, **extra) -> dict:
    """Standardised error result."""
    return {
        "success":    False,
        "insights":   "",
        "statistics": {},
        "charts":     [],
        "error":      message,
        **extra,
    }
