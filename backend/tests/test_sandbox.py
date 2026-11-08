"""
Tests for sandbox service — output parsing, error extraction,
statistics sanitisation. Does NOT require Docker (uses unit tests).
Run: cd backend && python -m pytest tests/test_sandbox.py -v
"""
import pytest
from app.services.sandbox_service import (
    _parse_output,
    _extract_error,
    _sanitize_statistics,
    _list_to_string,
    _to_docker_path,
    _error_result,
)


class TestParseOutput:
    """Test JSON parsing from sandbox stdout."""

    def test_valid_json_result(self):
        stdout = '{"success": true, "insights": "Found 10 rows.", "statistics": {"total": 10}, "charts": []}'
        result = _parse_output(stdout)
        assert result["success"] is True
        assert result["insights"] == "Found 10 rows."
        assert result["statistics"]["total"] == 10

    def test_json_with_leading_print_output(self):
        """AI code sometimes prints debug info before RESULT — we must still parse."""
        stdout = (
            "Processing data...\n"
            "Loaded 10 rows\n"
            '{"success": true, "insights": "Done.", "statistics": {}, "charts": []}\n'
        )
        result = _parse_output(stdout)
        assert result["success"] is True

    def test_empty_stdout(self):
        result = _parse_output("")
        assert result["success"] is False
        assert "no output" in result["error"].lower()

    def test_non_json_stdout(self):
        result = _parse_output("Hello World\nSome debug text")
        assert result["success"] is False

    def test_partial_json_skipped(self):
        stdout = '{"broken": \n{"success": true, "insights": "ok", "statistics": {}, "charts": []}'
        result = _parse_output(stdout)
        # Should find the valid JSON line
        assert result["success"] is True

    def test_statistics_sanitised_in_parse(self):
        """Arrays in statistics from parsed output should be sanitised."""
        stdout = '{"success": true, "insights": "ok", "statistics": {"rankings": [{"name": "Ali", "value": 10}]}, "charts": []}'
        result = _parse_output(stdout)
        assert result["success"] is True
        # After sanitisation, rankings should be a string, not a list
        assert isinstance(result["statistics"]["rankings"], str)
        assert "Ali" in result["statistics"]["rankings"]


class TestExtractError:
    """Test error extraction from exit codes and output."""

    def test_stderr_used_when_present(self):
        result = _extract_error(1, "", "NameError: name 'xyz' is not defined")
        assert "NameError" in result["error"]
        assert "exit 1" in result["error"]

    def test_traceback_extracted_from_stdout_when_stderr_empty(self):
        stdout = (
            "Loading data...\n"
            "Traceback (most recent call last):\n"
            "  File 'analysis.py', line 5\n"
            "AttributeError: 'DataFrame' object has no attribute 'gropby'\n"
        )
        result = _extract_error(1, stdout, "")
        assert "AttributeError" in result["error"]
        assert "gropby" in result["error"]
        assert "exit 1" in result["error"]

    def test_error_when_both_stdout_stderr_empty(self):
        result = _extract_error(1, "", "")
        assert "exit 1" in result["error"]
        assert "No error output" in result["error"]

    def test_exit_code_included(self):
        result = _extract_error(2, "", "some error")
        assert "exit 2" in result["error"]

    def test_error_result_structure(self):
        result = _error_result("Test error", error_type="test")
        assert result["success"] is False
        assert result["error"] == "Test error"
        assert result["error_type"] == "test"
        assert result["statistics"] == {}
        assert result["charts"] == []


class TestSanitizeStatistics:
    """Test statistics sanitisation."""

    def test_numbers_preserved(self):
        stats = {"total": 150, "avg": 45.5}
        result = _sanitize_statistics(stats)
        assert result["total"] == 150
        assert result["avg"] == 45.5

    def test_strings_preserved(self):
        stats = {"label": "Complete", "status": "OK"}
        result = _sanitize_statistics(stats)
        assert result["label"] == "Complete"

    def test_none_becomes_na(self):
        stats = {"missing": None}
        result = _sanitize_statistics(stats)
        assert result["missing"] == "N/A"

    def test_nan_becomes_na(self):
        stats = {"bad": float("nan")}
        result = _sanitize_statistics(stats)
        assert result["bad"] == "N/A"

    def test_infinity_becomes_na(self):
        stats = {"inf": float("inf")}
        result = _sanitize_statistics(stats)
        assert result["inf"] == "N/A"

    def test_list_of_objects_converted(self):
        stats = {"rankings": [{"name": "Ayesha", "value": 22}, {"name": "Nauman", "value": 20}]}
        result = _sanitize_statistics(stats)
        assert isinstance(result["rankings"], str)
        assert "Ayesha" in result["rankings"]
        assert "22" in result["rankings"]
        assert "[object Object]" not in result["rankings"]

    def test_list_of_primitives_converted(self):
        stats = {"tags": ["a", "b", "c"]}
        result = _sanitize_statistics(stats)
        assert isinstance(result["tags"], str)

    def test_nested_dict_converted(self):
        stats = {"breakdown": {"Q1": 100, "Q2": 200}}
        result = _sanitize_statistics(stats)
        assert isinstance(result["breakdown"], str)
        assert "Q1" in result["breakdown"]

    def test_non_dict_input_returns_empty(self):
        assert _sanitize_statistics(None) == {}  # type: ignore
        assert _sanitize_statistics([]) == {}    # type: ignore


class TestListToString:
    """Test list-to-string formatting."""

    def test_empty_list(self):
        assert _list_to_string([]) == ""

    def test_primitives(self):
        result = _list_to_string([1, 2, 3])
        assert "1" in result and "2" in result and "3" in result

    def test_name_value_objects(self):
        items = [{"name": "Ayesha", "value": 22}, {"name": "Nauman", "value": 20}]
        result = _list_to_string(items)
        assert "1. Ayesha — 22" in result
        assert "2. Nauman — 20" in result

    def test_label_value_objects(self):
        items = [{"label": "Product A", "value": 100}]
        result = _list_to_string(items)
        assert "Product A" in result


class TestDockerPathConversion:
    """Test path conversion logic."""

    def test_linux_path_unchanged(self):
        """On Linux, path should pass through unchanged."""
        import platform
        if platform.system() != "Windows":
            result = _to_docker_path("/tmp/datapilot/run123")
            assert result == "/tmp/datapilot/run123"

    def test_windows_path_converted(self):
        """Windows paths should be converted to Docker-compatible format."""
        import platform
        if platform.system() == "Windows":
            result = _to_docker_path("C:\\Users\\test\\data")
            assert result.startswith("/c/")
            assert "\\" not in result
