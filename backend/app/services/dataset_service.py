"""
Dataset Service — CSV validation, encoding detection, metadata extraction.
Phase 3 — Complete Implementation.
"""

import uuid
import io
from datetime import datetime
from pathlib import Path

import chardet
import pandas as pd

from app.config import settings
from app.models.dataset import ColumnInfo, DatasetMetadata, DatasetUploadResponse


def _detect_encoding(raw_bytes: bytes) -> str:
    """Detect file encoding using chardet, fallback to latin-1."""
    result = chardet.detect(raw_bytes[:50_000])  # sample first 50KB
    encoding = result.get("encoding") or "latin-1"
    # Normalize common variants
    if encoding.lower() in ("ascii", "utf-8-sig"):
        encoding = "utf-8"
    return encoding


def _read_csv(raw_bytes: bytes) -> pd.DataFrame:
    """Try reading CSV with detected encoding, fallback to latin-1."""
    encoding = _detect_encoding(raw_bytes)
    try:
        return pd.read_csv(io.BytesIO(raw_bytes), encoding=encoding)
    except Exception:
        return pd.read_csv(io.BytesIO(raw_bytes), encoding="latin-1")


def _extract_columns(df: pd.DataFrame) -> list[ColumnInfo]:
    """Extract per-column metadata."""
    columns = []
    for col in df.columns:
        sample = (
            df[col]
            .dropna()
            .head(5)
            .astype(str)
            .tolist()
        )
        columns.append(
            ColumnInfo(
                name=str(col),
                dtype=str(df[col].dtype),
                null_count=int(df[col].isnull().sum()),
                sample_values=sample,
            )
        )
    return columns


async def validate_and_process_csv(
    file_bytes: bytes,
    filename: str,
) -> DatasetUploadResponse:
    """
    Validates a CSV file and extracts metadata + preview.

    Steps:
      1. Check file size limit
      2. Validate .csv extension
      3. Detect encoding & parse with pandas
      4. Extract column info, dtypes, null counts, sample values
      5. Generate first-10-rows preview

    Returns DatasetUploadResponse.
    Raises ValueError for invalid files.
    """

    # ── 1. Size check ─────────────────────────────────────────────────────────
    if len(file_bytes) > settings.max_csv_size_bytes:
        raise ValueError(
            f"File too large. Maximum allowed size is {settings.max_csv_size_mb}MB."
        )

    # ── 2. Extension check ────────────────────────────────────────────────────
    if not filename.lower().endswith(".csv"):
        raise ValueError("Only CSV files are supported.")

    # ── 3. Parse CSV ──────────────────────────────────────────────────────────
    try:
        df = _read_csv(file_bytes)
    except Exception as e:
        raise ValueError(f"Could not parse CSV file: {str(e)}")

    if df.empty:
        raise ValueError("CSV file is empty.")

    if len(df.columns) == 0:
        raise ValueError("CSV file has no columns.")

    # ── 4. Extract metadata ───────────────────────────────────────────────────
    columns = _extract_columns(df)
    dataset_id = str(uuid.uuid4())

    # ── 5. Preview — first 10 rows as list of dicts ───────────────────────────
    preview = df.head(10).astype(str).fillna("").to_dict(orient="records")

    return DatasetUploadResponse(
        dataset_id=dataset_id,
        filename=filename,
        row_count=len(df),
        column_count=len(df.columns),
        columns=columns,
        preview=preview,
    )


def save_csv_to_disk(file_bytes: bytes, dataset_id: str) -> Path:
    """
    Saves uploaded CSV bytes to a persistent temp directory.
    Returns the path to the saved file.
    Used later when running analysis in the sandbox.
    """
    dataset_dir = Path(settings.temp_dir) / "datasets" / dataset_id
    dataset_dir.mkdir(parents=True, exist_ok=True)
    csv_path = dataset_dir / "input.csv"
    csv_path.write_bytes(file_bytes)
    return csv_path


def get_csv_path(dataset_id: str) -> Path:
    """Returns the stored CSV path for a given dataset_id."""
    return Path(settings.temp_dir) / "datasets" / dataset_id / "input.csv"


def get_dataframe(dataset_id: str) -> pd.DataFrame:
    """Loads the stored CSV as a DataFrame for metadata rebuilding."""
    csv_path = get_csv_path(dataset_id)
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset {dataset_id} not found.")
    raw = csv_path.read_bytes()
    return _read_csv(raw)
