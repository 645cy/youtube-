"""ContentProject Pydantic Schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class ContentProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    source_crawler_task_id: Optional[int] = None
    source_run_id: Optional[int] = None


class ContentProjectUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[str] = Field(default=None, pattern="^(draft|active|archived)$")
    script_json: Optional[str] = None
    storyboard_json: Optional[str] = None
    analysis_json: Optional[str] = None
    monetization_path_id: Optional[int] = None


class ContentProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    status: str
    source_crawler_task_id: Optional[int] = None
    source_run_id: Optional[int] = None
    script_json: Optional[str] = None
    storyboard_json: Optional[str] = None
    analysis_json: Optional[str] = None
    monetization_path_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    # 关联数据（由 API 层填充）
    source_task_name: Optional[str] = None
    source_run_status: Optional[str] = None


class ContentProjectList(BaseModel):
    items: list[ContentProjectRead]
    total: int
