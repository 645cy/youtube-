"""MetricHistory Pydantic Schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MetricHistoryCreate(BaseModel):
    """创建指标历史记录."""
    channel_id: Optional[int] = None
    video_id: Optional[int] = None
    metric_type: str = Field(..., pattern="^(subscriber|view|like|comment)$")
    value: float


class MetricHistoryRead(BaseModel):
    """指标历史响应."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel_id: Optional[int] = None
    video_id: Optional[int] = None
    metric_type: str
    value: float
    recorded_at: datetime
