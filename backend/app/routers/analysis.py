"""
Analysis Router — Full AI analysis workflow.
Phase 4+5+6+7+8 — Complete Implementation.
"""

import json
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.models.user import AuthenticatedUser
from app.models.analysis import (
    AnalysisRequest, AnalysisResult, AnalysisHistoryItem, ChartData,
)
from app.services.ai_service import generate_analysis_code, generate_error_correction
from app.services.sandbox_service import execute_in_sandbox
from app.services.dataset_service import get_csv_path, get_dataframe
from app.utils.code_validator import validate_code
from app.config import settings

router = APIRouter()
MAX_RETRIES = 2

# Error types not worth retrying — a code fix won't help these
NON_RETRYABLE = {
    "timeout", "docker_unavailable", "image_not_found",
    "file_not_found", "setup_error", "docker_api_error",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _dataset_meta_path(dataset_id: str) -> Path:
    return Path(settings.temp_dir) / "datasets" / dataset_id / "meta.json"


def _analysis_store_path(user_uid: str) -> Path:
    path = Path(settings.temp_dir) / "analyses" / user_uid
    path.mkdir(parents=True, exist_ok=True)
    return path


def _save_analysis(user_uid: str, result: AnalysisResult) -> None:
    path = _analysis_store_path(user_uid) / f"{result.analysis_id}.json"
    path.write_text(result.model_dump_json(), encoding="utf-8")


def _load_analyses(user_uid: str) -> list[AnalysisResult]:
    store = _analysis_store_path(user_uid)
    results = []
    for f in store.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            results.append(AnalysisResult(**data))
        except Exception:
            continue
    return sorted(results, key=lambda r: r.created_at, reverse=True)


def _build_dataset_metadata(dataset_id: str) -> dict:
    meta_path = _dataset_meta_path(dataset_id)
    if not meta_path.exists():
        raise FileNotFoundError(f"Dataset {dataset_id} not found.")

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    try:
        df = get_dataframe(dataset_id)
        columns = []
        for col in df.columns:
            sample = df[col].dropna().head(5).astype(str).tolist()
            columns.append({
                "name": str(col),
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isnull().sum()),
                "sample_values": sample,
            })
        meta["columns"] = columns
    except Exception as e:
        print(f"[Analysis] Warning: could not reload columns: {e}")
        meta["columns"] = []
    return meta


def _parse_charts(raw_charts: list) -> list[ChartData]:
    """Parse chart data, normalising field names and dropping malformed entries."""
    result = []
    for c in raw_charts:
        try:
            data = c.get("data", [])
            if not isinstance(data, list):
                continue
            cleaned = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                name = (item.get("name") or item.get("label")
                        or item.get("category") or str(list(item.values())[0]))
                raw_val = (
                    item.get("value") if item.get("value") is not None
                    else item.get("count") if item.get("count") is not None
                    else item.get("y") if item.get("y") is not None
                    else list(item.values())[1] if len(item) > 1 else 0
                )
                try:
                    fval = float(raw_val)
                    fval = fval if fval == fval else 0.0  # NaN check
                except (TypeError, ValueError):
                    fval = 0.0
                cleaned.append({"name": str(name), "value": fval})
            if not cleaned:
                continue
            result.append(ChartData(
                type=c.get("type", "bar"),
                title=c.get("title", "Chart"),
                x_label=c.get("x_label", ""),
                y_label=c.get("y_label", ""),
                data=cleaned,
            ))
        except Exception as e:
            print(f"[Analysis] Skipped malformed chart: {e}")
    return result


def _is_retryable(sandbox_result: dict) -> bool:
    """Only retry execution/code errors — not infra failures."""
    error_type = sandbox_result.get("error_type", "")
    if error_type in NON_RETRYABLE:
        return False
    error_msg = sandbox_result.get("error", "")
    return bool(error_msg)


def _user_facing_error(sandbox_result: dict) -> str:
    """Turn technical error messages into user-friendly ones."""
    error_type = sandbox_result.get("error_type", "")
    raw = sandbox_result.get("error", "Analysis failed.")
    if error_type == "timeout":
        return ("Analysis timed out. Try a simpler or more focused question, "
                "or reduce the dataset size.")
    if error_type == "docker_unavailable":
        return "Sandbox is unavailable. Please contact support."
    if error_type == "image_not_found":
        return "Sandbox environment not ready. Please contact support."
    if error_type == "file_not_found":
        return "Dataset file not found. Please re-upload your CSV."
    # For execution errors, show a truncated but informative message
    if len(raw) > 500:
        return raw[:500] + "…"
    return raw


# ── POST /analysis/run ─────────────────────────────────────────────────────────

@router.post("/run", response_model=AnalysisResult, status_code=status.HTTP_200_OK)
async def run_analysis(
    request: AnalysisRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Full AI analysis workflow with retries for fixable code errors."""
    start_time = time.time()

    # 1. Verify dataset ownership
    meta_path = _dataset_meta_path(request.dataset_id)
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Dataset not found.")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("user_uid") != current_user.uid:
        raise HTTPException(status_code=403, detail="Access denied.")

    # 2. Load dataset metadata for AI prompt
    try:
        dataset_metadata = _build_dataset_metadata(request.dataset_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not load dataset: {e}")

    csv_path = str(get_csv_path(request.dataset_id))

    # 3. Generate Python code via Vultr AI
    try:
        code = await generate_analysis_code(request.prompt, dataset_metadata)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI code generation failed: {e}")

    # 4. Validate code safety
    try:
        validate_code(code)
    except ValueError as e:
        # Try to fix the safety violation once before giving up
        try:
            code = await generate_error_correction(str(e), str(e), dataset_metadata)
            validate_code(code)
        except Exception:
            raise HTTPException(
                status_code=422,
                detail=f"Generated code failed safety check: {e}",
            )

    # 5. Execute + retry loop
    sandbox_result = None
    retry_count = 0
    last_error = ""

    for attempt in range(MAX_RETRIES + 1):
        sandbox_result = await execute_in_sandbox(code, csv_path)

        if sandbox_result.get("success"):
            break

        last_error = sandbox_result.get("error", "")
        print(f"[Analysis] Attempt {attempt+1} failed: {last_error[:200]}")

        # Don't retry infra failures
        if not _is_retryable(sandbox_result):
            break

        if attempt < MAX_RETRIES:
            retry_count += 1
            try:
                corrected = await generate_error_correction(
                    code, last_error, dataset_metadata
                )
                validate_code(corrected)
                code = corrected
            except Exception as fix_err:
                print(f"[Analysis] Error correction failed: {fix_err}")
                break

    # 6. Build result
    execution_time_ms = int((time.time() - start_time) * 1000)
    analysis_id = str(uuid.uuid4())

    if sandbox_result and sandbox_result.get("success"):
        result = AnalysisResult(
            analysis_id=analysis_id,
            dataset_id=request.dataset_id,
            prompt=request.prompt,
            insights=sandbox_result.get("insights", "Analysis complete."),
            statistics=sandbox_result.get("statistics", {}),
            charts=_parse_charts(sandbox_result.get("charts", [])),
            execution_time_ms=execution_time_ms,
            retry_count=retry_count,
        )
    else:
        friendly = _user_facing_error(sandbox_result) if sandbox_result else "Analysis failed."
        result = AnalysisResult(
            analysis_id=analysis_id,
            dataset_id=request.dataset_id,
            prompt=request.prompt,
            insights=f"Analysis could not be completed.\n{friendly}",
            statistics={},
            charts=[],
            execution_time_ms=execution_time_ms,
            retry_count=retry_count,
        )

    _save_analysis(current_user.uid, result)
    return result


# ── GET /analysis/history ──────────────────────────────────────────────────────

@router.get("/history", response_model=list[AnalysisHistoryItem])
async def get_analysis_history(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    analyses = _load_analyses(current_user.uid)
    return [
        AnalysisHistoryItem(
            analysis_id=a.analysis_id,
            dataset_id=a.dataset_id,
            prompt=a.prompt,
            chart_count=len(a.charts),
            created_at=str(a.created_at),
        )
        for a in analyses
    ]


# ── GET /analysis/{analysis_id} ────────────────────────────────────────────────

@router.get("/{analysis_id}", response_model=AnalysisResult)
async def get_analysis_result(
    analysis_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    store = _analysis_store_path(current_user.uid)
    result_file = store / f"{analysis_id}.json"
    if not result_file.exists():
        raise HTTPException(status_code=404, detail="Analysis not found.")
    data = json.loads(result_file.read_text(encoding="utf-8"))
    return AnalysisResult(**data)
