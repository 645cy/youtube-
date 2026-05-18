"""CrawlerTask Pydantic Schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from apps.api.config import settings


class CrawlerTaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    task_type: str = Field(
        settings.DEFAULT_CRAWLER_TASK_TYPE,
        pattern="^(channel_latest|keyword_search|channel_stats|channel_discovery)$",
    )
    target: str = Field(..., min_length=1, max_length=500)
    frequency: str = settings.DEFAULT_CRAWLER_FREQUENCY
    config: Dict[str, Any] = Field(default_factory=dict)


class CrawlerTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    task_type: str
    target: str
    frequency: str
    status: str
    config_json: Optional[str] = None
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    latest_run_status: Optional[str] = None
    latest_run_message: Optional[str] = None
    latest_items_found: int = 0


class CrawlerTaskRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    status: str
    source_status: Optional[str] = None
    message: Optional[str] = None
    items_found: int
    result_json: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
