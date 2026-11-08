"""
Sandbox Runner — Executes AI-generated analysis code safely.

This script runs INSIDE the Docker container.
It reads the analysis code from /code/analysis.py,
executes it, and outputs the result as JSON to stdout.

The AI-generated code must assign its result to a variable
named `RESULT` following this schema:
{
    "insights": "...",
    "statistics": {...},
    "charts": [{"type": "...", "title": "...", "data": [...]}]
}
"""

import json
import sys
import traceback
from pathlib import Path


class _NumpyEncoder(json.JSONEncoder):
    """Converts NumPy / Pandas types to JSON-serializable Python types."""

    def default(self, obj):
        # NumPy scalar types
        try:
            import numpy as np
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, np.bool_):
                return bool(obj)
        except ImportError:
            pass

        # Pandas Timestamp
        try:
            import pandas as pd
            if isinstance(obj, pd.Timestamp):
                return obj.isoformat()
        except ImportError:
            pass

        return super().default(obj)


def _output(payload: dict) -> None:
    """Writes the final JSON result to stdout."""
    print(json.dumps(payload, cls=_NumpyEncoder), flush=True)


def main() -> None:
    code_path = Path("/code/analysis.py")

    if not code_path.exists():
        _output({"success": False, "error": "analysis.py not found in /code/"})
        sys.exit(1)

    code = code_path.read_text(encoding="utf-8")

    # Execution namespace — expose the input CSV path
    namespace = {"__builtins__": __builtins__, "INPUT_CSV": "/data/input.csv"}

    try:
        exec(compile(code, "analysis.py", "exec"), namespace)  # noqa: S102
    except Exception:
        _output({
            "success": False,
            "error": traceback.format_exc(),
        })
        sys.exit(1)

    result = namespace.get("RESULT")

    if result is None:
        _output({
            "success": False,
            "error": "Generated code did not produce a RESULT variable.",
        })
        sys.exit(1)

    _output({"success": True, **result})


if __name__ == "__main__":
    main()
