import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status

from app.dependencies import get_current_user
from app.models.user import AuthenticatedUser
from app.models.dataset import DatasetUploadResponse, DatasetListItem
from app.services.dataset_service import (
    validate_and_process_csv,
    save_csv_to_disk,
    get_csv_path,
)
from app.config import settings

router = APIRouter()


def _meta_path(dataset_id: str) -> Path:
    """Path to the JSON metadata file for a dataset."""
    return Path(settings.temp_dir) / "datasets" / dataset_id / "meta.json"


def _save_meta(dataset_id: str, user_uid: str, response: DatasetUploadResponse) -> None:
    """Persist dataset metadata to disk so it survives across requests."""
    meta = {
        "dataset_id":   response.dataset_id,
        "user_uid":     user_uid,
        "filename":     response.filename,
        "row_count":    response.row_count,
        "column_count": response.column_count,
        "uploaded_at":  datetime.utcnow().isoformat(),
    }
    _meta_path(dataset_id).write_text(json.dumps(meta), encoding="utf-8")


def _load_user_datasets(user_uid: str) -> list[dict]:
    """Load all dataset metadata files belonging to a user."""
    datasets_root = Path(settings.temp_dir) / "datasets"
    results = []
    if not datasets_root.exists():
        return results
    for meta_file in datasets_root.glob("*/meta.json"):
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            if meta.get("user_uid") == user_uid:
                results.append(meta)
        except Exception:
            continue
    return results


# ── POST /datasets/upload ─────────────────────────────────────────────────────

@router.post("/upload", response_model=DatasetUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Upload a CSV file for analysis.
    Validates format, size, and encoding.
    Returns metadata + preview of the dataset.
    """
    file_bytes = await file.read()
    filename = file.filename or "upload.csv"

    # Validate & extract metadata
    try:
        response = await validate_and_process_csv(file_bytes, filename)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    # Persist CSV + metadata to disk
    save_csv_to_disk(file_bytes, response.dataset_id)
    _save_meta(response.dataset_id, current_user.uid, response)

    return response


# ── GET /datasets/ ────────────────────────────────────────────────────────────

@router.get("/", response_model=list[DatasetListItem])
async def list_datasets(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Returns all datasets uploaded by the authenticated user."""
    metas = _load_user_datasets(current_user.uid)
    return [
        DatasetListItem(
            dataset_id=m["dataset_id"],
            filename=m["filename"],
            row_count=m["row_count"],
            column_count=m["column_count"],
            uploaded_at=m.get("uploaded_at", datetime.utcnow().isoformat()),
        )
        for m in metas
    ]


# ── DELETE /datasets/{dataset_id} ─────────────────────────────────────────────

@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Deletes a dataset — only the owner can delete it."""
    meta_file = _meta_path(dataset_id)

    if not meta_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    if meta.get("user_uid") != current_user.uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    import shutil
    dataset_dir = Path(settings.temp_dir) / "datasets" / dataset_id
    shutil.rmtree(dataset_dir, ignore_errors=True)
