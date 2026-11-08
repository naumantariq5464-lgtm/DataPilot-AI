"""
AI Service — Vultr Serverless Inference integration.
Phase 4 — Complete Implementation.

Uses OpenAI SDK with base_url pointed at Vultr endpoint.
Credentials stay on backend only — never exposed to frontend or sandbox.
"""

import re
from openai import AsyncOpenAI

from app.config import settings

# ── Vultr client (OpenAI-compatible) ─────────────────────────────────────────

_client = AsyncOpenAI(
    api_key=settings.vultr_inference_api_key,
    base_url=settings.vultr_inference_base_url,
)

# ── System prompt for code generation ────────────────────────────────────────

_CODE_SYSTEM_PROMPT = """You are an expert Python data analyst. Your ONLY job is to write clean, executable Python code that directly answers the user's question about a CSV dataset.

═══════════════════════════════════════════════
PRIORITY RULE — THE MOST IMPORTANT INSTRUCTION
═══════════════════════════════════════════════
You MUST answer the user's EXACT question. Do NOT write generic descriptive statistics unless the user specifically asks for them.

Examples:
- User asks "which product sold most?" → Find and return that product name + quantity. Do NOT return averages for all products.
- User asks "rank employees by salary" → Sort and return the ranked list. Do NOT return column means.
- User asks "what is the average order value?" → Calculate and return that one number.
- User asks "show trends by month" → Group by month, calculate the requested metric per month.

═══════════════════════════
ENVIRONMENT & IMPORTS
═══════════════════════════
1. The CSV is already available — load it with:
   df = pd.read_csv(INPUT_CSV)
   (INPUT_CSV is a string variable already set for you)

2. ALLOWED imports only:
   pandas, numpy, json, math, statistics, collections, itertools, datetime

3. NEVER import: os, sys, subprocess, socket, shutil, pathlib, matplotlib, seaborn, plotly, requests

═══════════════════════════
RESULT VARIABLE — REQUIRED
═══════════════════════════
You MUST assign a variable named RESULT at the END of your code with this exact structure:

RESULT = {
    "insights": "A clear 2-4 sentence explanation of what was found, directly answering the user's question.",
    "statistics": {
        "metric_name": scalar_value,   # int or float ONLY
        "label_metric": "string value" # short string ONLY
    },
    "charts": [
        {
            "type": "bar",
            "title": "Descriptive Chart Title",
            "x_label": "X Axis Label",
            "y_label": "Y Axis Label",
            "data": [{"name": "Category", "value": 123}, ...]
        }
    ]
}

═══════════════════════════════════════════════
STATISTICS VALUES — STRICT TYPE RULES
═══════════════════════════════════════════════
statistics values MUST be ONLY:
  ✅ int or float (scalar numbers)
  ✅ short strings (text, labels, names)

statistics values MUST NEVER be:
  ❌ lists or arrays  →  [1, 2, 3]
  ❌ dicts or objects →  {"a": 1}
  ❌ None / NaN

RANKINGS — always convert to a string:
  CORRECT:
    sorted_df = df.sort_values('salary', ascending=False)
    ranking = " | ".join(
        f"{i+1}. {row['name']} ({row['salary']:,.0f})"
        for i, (_, row) in enumerate(sorted_df.head(10).iterrows())
    )
    RESULT["statistics"]["top_earners"] = ranking

  INCORRECT — will break the UI:
    RESULT["statistics"]["top_earners"] = [{"name": "Ali", "value": 50000}]  ❌

═══════════════════════════
TIES — ALWAYS HANDLE THEM
═══════════════════════════
When finding "most common", "top", "highest frequency" categorical values:
  counts = df['col'].value_counts()
  max_val = int(counts.iloc[0])
  top_items = counts[counts == max_val]
  result_str = ", ".join(f"{k} ({v})" for k, v in top_items.items())
  NEVER use .mode()[0] or .idxmax() alone — they silently drop ties.

═══════════════════════════
CHART SELECTION RULES
═══════════════════════════
Choose chart type based on the question and data:
  • Category comparison (sales by product, count by department) → "bar" or "horizontal_bar"
  • Trend over time (monthly sales, weekly orders)              → "line" or "area"
  • Parts of a whole (market share, category proportion)        → "pie" or "donut"
  • Distribution of one numeric column (ages, prices)           → "histogram"
  • Relationship between two numeric columns                    → "scatter"
  • Comparison of distributions across groups                   → "boxplot"
  • Correlation matrix of numeric columns                       → "heatmap"
  • Multiple metrics per category                               → "grouped_bar"

Chart data must ALWAYS be a list of {"name": label, "value": number} objects.
Generate 1–3 charts per analysis. Each chart must be relevant to the user's question.

═══════════════════════════
MISSING VALUES
═══════════════════════════
- Use .dropna() before calculations on columns that may have nulls.
- Use .fillna(0) for numeric aggregations where 0 is a safe default.
- Check if a required column exists before using it; if missing, explain in insights.

═══════════════════════════
NUMPY TYPE CONVERSION
═══════════════════════════
Before assigning to RESULT, convert numpy types:
  int(np_value)    for integers
  float(np_value)  for floats
  str(np_value)    for everything else

Or use: df.to_dict(orient='records') which handles this automatically for chart data.

═══════════════════════════
OUTPUT FORMAT
═══════════════════════════
Output ONLY the Python code.
Do NOT include markdown code fences (```python).
Do NOT include explanations or comments outside the code.
Do NOT add print() statements — the runner captures RESULT automatically.
The LAST statement in your code MUST be the RESULT = {...} assignment.
"""

_ERROR_CORRECTION_PROMPT = """You are an expert Python data analyst. The code below failed. Fix it.

ORIGINAL CODE:
{original_code}

ERROR:
{error_message}

RULES:
- Fix ONLY what caused the error
- Keep the same RESULT structure
- Do NOT use: os, sys, subprocess, socket, matplotlib, seaborn, plotly
- statistics values must be int, float or string — never lists or dicts
- Output ONLY the fixed Python code. No markdown fences. No explanations.
"""


# ── Code extraction helper ────────────────────────────────────────────────────

def _extract_code(raw_response: str) -> str:
    """
    Strip markdown code fences if the model wraps output despite instructions.
    Also removes any leading/trailing blank lines.
    """
    # Remove ```python ... ``` or ``` ... ```
    cleaned = re.sub(r"^```(?:python)?\s*\n?", "", raw_response.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned.strip(), flags=re.MULTILINE)
    return cleaned.strip()


# ── Public API ────────────────────────────────────────────────────────────────

async def generate_analysis_code(prompt: str, dataset_metadata: dict) -> str:
    """
    Sends a code-generation prompt to Vultr Serverless Inference.
    Returns clean, executable Python code (no markdown fences).
    """
    columns_info = "\n".join(
        f"  - {col['name']} ({col['dtype']}, {col['null_count']} nulls)"
        f" — sample values: {col['sample_values'][:3]}"
        for col in dataset_metadata.get("columns", [])
    )

    user_message = (
        f"Dataset: {dataset_metadata.get('filename', 'data.csv')}\n"
        f"Rows: {dataset_metadata.get('row_count', '?')} | "
        f"Columns: {dataset_metadata.get('column_count', '?')}\n\n"
        f"Column details:\n{columns_info}\n\n"
        f"USER'S QUESTION (answer this EXACTLY — do not substitute generic stats):\n"
        f"{prompt}\n\n"
        f"Write Python code that directly answers the question above.\n"
        f"Use the exact column names shown. Handle missing values. "
        f"Return the RESULT variable as the final statement."
    )

    response = await _client.chat.completions.create(
        model=settings.vultr_model_name,
        messages=[
            {"role": "system", "content": _CODE_SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        temperature=0.1,   # very low — we want deterministic, correct code
        max_tokens=2048,
    )

    raw_code = response.choices[0].message.content or ""
    return _extract_code(raw_code)


async def generate_error_correction(
    original_code: str,
    error_message: str,
    dataset_metadata: dict,
) -> str:
    """
    Sends failed code + error back to AI for correction.
    Called by the retry loop in the analysis router.
    """
    user_message = _ERROR_CORRECTION_PROMPT.format(
        original_code=original_code,
        error_message=error_message[:1500],  # cap error to avoid token waste
    )

    response = await _client.chat.completions.create(
        model=settings.vultr_model_name,
        messages=[
            {"role": "system", "content": _CODE_SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        temperature=0.1,
        max_tokens=2048,
    )

    raw_code = response.choices[0].message.content or ""
    return _extract_code(raw_code)
