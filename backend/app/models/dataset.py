from pydantic import BaseModel, Field
from datetime import datetime


class ColumnInfo(BaseModel):
    """Metadata for a single CSV column."""

    name: str
    dtype: str
    null_count: int
    sample_values: list[str]


class DatasetMetadata(BaseModel):
    """Full metadata extracted from an uploaded CSV."""

    dataset_id: str
    filename: str
    row_count: int
    column_count: int
    columns: list[ColumnInfo]
    size_bytes: int
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class DatasetUploadResponse(BaseModel):
    """Response returned after a successful CSV upload."""

    dataset_id: str
    filename: str
    row_count: int
    column_count: int
    columns: list[ColumnInfo]
    preview: list[dict]  # First 10 rows as list of dicts


class DatasetListItem(BaseModel):
    """Summary item shown in the dataset list."""

    dataset_id: str
    filename: str
    row_count: int
    column_count: int
    uploaded_at: datetime
