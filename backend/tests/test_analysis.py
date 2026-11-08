"""
Tests for analysis workflow — code validator, chart parsing,
retry logic, error classification.
Run: cd backend && python -m pytest tests/test_analysis.py -v
"""
import pytest
from app.utils.code_validator import validate_code
from app.routers.analysis import _parse_charts, _is_retryable, _user_facing_error


class TestCodeValidator:
    """Test AST-based code safety validator."""

    def test_valid_pandas_code_passes(self):
        code = """
import pandas as pd
import numpy as np
df = pd.read_csv(INPUT_CSV)
total = int(df['Revenue'].sum())
RESULT = {"insights": "ok", "statistics": {"total": total}, "charts": []}
"""
        validate_code(code)  # should not raise

    def test_os_import_blocked(self):
        code = "import os\nRESULT = {}"
        with pytest.raises(ValueError, match="os"):
            validate_code(code)

    def test_sys_import_blocked(self):
        code = "import sys\nRESULT = {}"
        with pytest.raises(ValueError, match="sys"):
            validate_code(code)

    def test_subprocess_blocked(self):
        code = "import subprocess\nRESULT = {}"
        with pytest.raises(ValueError, match="subprocess"):
            validate_code(code)

    def test_eval_blocked(self):
        code = "x = eval('1+1')\nRESULT = {}"
        with pytest.raises(ValueError, match="eval"):
            validate_code(code)

    def test_exec_blocked(self):
        code = "exec('x=1')\nRESULT = {}"
        with pytest.raises(ValueError, match="exec"):
            validate_code(code)

    def test_syntax_error_caught(self):
        code = "df = pd.read_csv(INPUT_CSV\nRESULT = {}"
        with pytest.raises(ValueError, match="Syntax"):
            validate_code(code)

    def test_pathlib_blocked(self):
        code = "from pathlib import Path\nRESULT = {}"
        with pytest.raises(ValueError, match="pathlib"):
            validate_code(code)

    def test_allowed_imports_pass(self):
        code = """
import pandas as pd
import numpy as np
import json
import math
import statistics
from collections import Counter
from itertools import groupby
RESULT = {"insights": "ok", "statistics": {}, "charts": []}
"""
        validate_code(code)  # no exception


class TestParseCharts:
    """Test chart data parsing and normalisation."""

    def test_valid_bar_chart(self):
        raw = [{
            "type": "bar",
            "title": "Sales by Product",
            "x_label": "Product",
            "y_label": "Revenue",
            "data": [
                {"name": "Laptop", "value": 250000},
                {"name": "Phone", "value": 180000},
            ]
        }]
        charts = _parse_charts(raw)
        assert len(charts) == 1
        assert charts[0].type == "bar"
        assert charts[0].data[0]["name"] == "Laptop"
        assert charts[0].data[0]["value"] == 250000.0

    def test_normalises_count_field(self):
        """Charts with 'count' instead of 'value' should work."""
        raw = [{
            "type": "bar",
            "title": "Count by Dept",
            "x_label": "Dept", "y_label": "Count",
            "data": [{"name": "Engineering", "count": 5}]
        }]
        charts = _parse_charts(raw)
        assert charts[0].data[0]["value"] == 5.0

    def test_normalises_label_field(self):
        """Charts with 'label' instead of 'name' should work."""
        raw = [{
            "type": "pie",
            "title": "Market Share",
            "x_label": "", "y_label": "",
            "data": [{"label": "Product A", "value": 40}]
        }]
        charts = _parse_charts(raw)
        assert charts[0].data[0]["name"] == "Product A"

    def test_empty_data_skipped(self):
        raw = [{"type": "bar", "title": "Empty", "x_label": "", "y_label": "", "data": []}]
        charts = _parse_charts(raw)
        assert len(charts) == 0

    def test_nan_value_becomes_zero(self):
        raw = [{
            "type": "bar",
            "title": "Test",
            "x_label": "", "y_label": "",
            "data": [{"name": "A", "value": float("nan")}]
        }]
        charts = _parse_charts(raw)
        assert charts[0].data[0]["value"] == 0.0

    def test_malformed_chart_skipped(self):
        raw = [
            None,
            {"type": "bar", "title": "Good", "x_label": "", "y_label": "",
             "data": [{"name": "A", "value": 1}]},
        ]
        charts = _parse_charts(raw)  # type: ignore
        assert len(charts) == 1

    def test_multiple_charts(self):
        raw = [
            {"type": "bar", "title": "Chart 1", "x_label": "", "y_label": "",
             "data": [{"name": "A", "value": 1}]},
            {"type": "line", "title": "Chart 2", "x_label": "", "y_label": "",
             "data": [{"name": "B", "value": 2}]},
        ]
        charts = _parse_charts(raw)
        assert len(charts) == 2
        assert charts[0].type == "bar"
        assert charts[1].type == "line"


class TestRetryLogic:
    """Test which error types trigger retries."""

    def test_execution_error_is_retryable(self):
        result = {
            "success": False,
            "error": "Code execution failed (exit 1): AttributeError",
            "error_type": "execution_error",
        }
        assert _is_retryable(result) is True

    def test_timeout_not_retryable(self):
        result = {"success": False, "error": "timed out", "error_type": "timeout"}
        assert _is_retryable(result) is False

    def test_docker_unavailable_not_retryable(self):
        result = {"success": False, "error": "Docker unavailable", "error_type": "docker_unavailable"}
        assert _is_retryable(result) is False

    def test_image_not_found_not_retryable(self):
        result = {"success": False, "error": "Image not found", "error_type": "image_not_found"}
        assert _is_retryable(result) is False

    def test_file_not_found_not_retryable(self):
        result = {"success": False, "error": "CSV not found", "error_type": "file_not_found"}
        assert _is_retryable(result) is False

    def test_parse_error_is_retryable(self):
        result = {"success": False, "error": "Could not parse output", "error_type": "parse_error"}
        assert _is_retryable(result) is True

    def test_empty_error_not_retryable(self):
        result = {"success": False, "error": "", "error_type": ""}
        assert _is_retryable(result) is False


class TestUserFacingErrors:
    """Test user-friendly error message generation."""

    def test_timeout_message(self):
        result = {"error_type": "timeout", "error": "timed out after 120s"}
        msg = _user_facing_error(result)
        assert "timed out" in msg.lower()

    def test_file_not_found_message(self):
        result = {"error_type": "file_not_found", "error": "not found"}
        msg = _user_facing_error(result)
        assert "upload" in msg.lower() or "not found" in msg.lower()

    def test_long_error_truncated(self):
        long_error = "Error: " + ("x" * 1000)
        result = {"error_type": "execution_error", "error": long_error}
        msg = _user_facing_error(result)
        assert len(msg) <= 503  # 500 + "…"
