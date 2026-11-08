"""
Tests for CSV upload, validation, and dataset_service.
Run: cd backend && python -m pytest tests/test_upload.py -v
"""
import io
import pytest

# ── CSV fixtures ──────────────────────────────────────────────────────────────

EMPLOYEE_CSV = b"""Employee,Department,Salary,Projects_Completed
Ayesha,Engineering,95000,22
Nauman,Engineering,88000,20
Sara,Marketing,72000,18
Hamza,Sales,65000,16
Ali,Engineering,82000,15
Bilal,Marketing,68000,14
Ahmed,Sales,60000,12
Hina,HR,55000,11
Usman,HR,52000,9
Zain,Sales,48000,7
"""

SALES_CSV = b"""Product,City,Quantity,Revenue
Laptop,Karachi,50,250000
Phone,Lahore,120,180000
Tablet,Islamabad,30,90000
Laptop,Lahore,40,200000
Phone,Karachi,150,225000
Tablet,Karachi,25,75000
Laptop,Islamabad,35,175000
Phone,Islamabad,90,135000
"""

MISSING_VALUES_CSV = b"""Name,Score,Grade
Alice,85,A
Bob,,B
Charlie,92,
,78,C
Eve,88,A
"""

UNUSUAL_COLUMNS_CSV = b"""First Name,Last Name,Age (Years),Annual Income ($),Join Date
Ahmed,Khan,28,65000,2020-01-15
Fatima,Ali,32,78000,2019-06-20
Omar,Farooq,25,52000,2021-03-10
"""

EMPTY_CSV = b""

SINGLE_ROW_CSV = b"Name,Value\nTest,1\n"


# ── Tests ─────────────────────────────────────────────────────────────────────

import asyncio
import pytest
from app.services.dataset_service import validate_and_process_csv


def run(coro):
    return asyncio.run(coro)


class TestCSVUpload:
    """Test CSV validation and metadata extraction."""

    def test_valid_employee_csv(self):
        result = run(validate_and_process_csv(EMPLOYEE_CSV, "employees.csv"))
        assert result.row_count == 10
        assert result.column_count == 4
        assert result.filename == "employees.csv"
        col_names = [c.name for c in result.columns]
        assert "Employee" in col_names
        assert "Salary" in col_names
        assert len(result.preview) <= 10

    def test_valid_sales_csv(self):
        result = run(validate_and_process_csv(SALES_CSV, "sales.csv"))
        assert result.row_count == 8
        assert result.column_count == 4
        col_names = [c.name for c in result.columns]
        assert "Product" in col_names
        assert "Revenue" in col_names

    def test_missing_values_csv(self):
        """CSV with missing values should parse, not raise."""
        result = run(validate_and_process_csv(MISSING_VALUES_CSV, "missing.csv"))
        assert result.row_count == 5
        # Null counts should be non-zero
        null_counts = {c.name: c.null_count for c in result.columns}
        assert null_counts["Score"] >= 1
        assert null_counts["Grade"] >= 1

    def test_unusual_column_names(self):
        """Columns with spaces and special chars should be preserved."""
        result = run(validate_and_process_csv(UNUSUAL_COLUMNS_CSV, "unusual.csv"))
        assert result.row_count == 3
        col_names = [c.name for c in result.columns]
        assert "First Name" in col_names
        assert "Annual Income ($)" in col_names

    def test_empty_file_rejected(self):
        with pytest.raises(ValueError):
            run(validate_and_process_csv(EMPTY_CSV, "empty.csv"))

    def test_non_csv_extension_rejected(self):
        with pytest.raises(ValueError, match="CSV"):
            run(validate_and_process_csv(EMPLOYEE_CSV, "data.xlsx"))

    def test_single_row_csv(self):
        """Single data row should parse."""
        result = run(validate_and_process_csv(SINGLE_ROW_CSV, "single.csv"))
        assert result.row_count == 1
        assert result.column_count == 2

    def test_dtypes_detected(self):
        """Numeric and string columns should have correct dtype hints."""
        result = run(validate_and_process_csv(EMPLOYEE_CSV, "emp.csv"))
        dtype_map = {c.name: c.dtype for c in result.columns}
        # Salary should be numeric
        assert "int" in dtype_map["Salary"] or "float" in dtype_map["Salary"]
        # Employee name should be text type (object in pandas 1/2, str in pandas 3+)
        assert "object" in dtype_map["Employee"] or "str" in dtype_map["Employee"]

    def test_sample_values_present(self):
        result = run(validate_and_process_csv(EMPLOYEE_CSV, "emp.csv"))
        for col in result.columns:
            assert isinstance(col.sample_values, list)
            assert len(col.sample_values) > 0
