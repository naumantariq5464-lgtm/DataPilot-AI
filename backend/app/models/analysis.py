from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any


class AnalysisRequest(BaseModel):
    """Incoming analysis request from the frontend."""

    dataset_id: str
    prompt: str = Field(min_length=5, max_length=1000)


class ChartData(BaseModel):
    """Data for a single chart to be rendered on the frontend."""

    type: str           # bar | line | area | pie | donut | scatter |
                        # histogram | boxplot | heatmap | grouped_bar
    title: str
    x_label: str = ""
    y_label: str = ""
    data: list[dict[str, Any]]


class AnalysisResult(BaseModel):
    """Structured result returned to the frontend after analysis."""

    analysis_id: str
    dataset_id: str
    prompt: str
    insights: str                        # AI-generated text explanation
    statistics: dict[str, Any] = {}      # Key metrics / summary stats
    charts: list[ChartData] = []         # Dynamic chart data
    execution_time_ms: int = 0
    retry_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AnalysisHistoryItem(BaseModel):
    """Summary item shown in analysis history list."""

    analysis_id: str
    dataset_id: str
    prompt: str
    chart_count: int
    created_at: datetime
