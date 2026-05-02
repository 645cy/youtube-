"""MonitorJob Pydantic Schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MonitorJobCreate(BaseModel):
    """创建监控任务."""
    channel_id: int = Field(..., gt=0)
    job_type: str = Field(..., pattern="^(stats|new_videos|comments|search)$")
    frequency: str = "daily"
    config_json: Optional[str] = None


class MonitorJobRead(BaseModel):
    """监控任务响应."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel_id: int
    job_type: str
    frequency: str
    status: str
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    config_json: Optional[str] = None
    created_at: datetime


class MonitorWithChannel(BaseModel):
    """监控任务 + 关联频道信息."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel_id: int
    channel_name: str = ""
    channel_thumbnail: str = ""
    subscriber_count: int = 0
    job_type: str
    frequency: str
    status: str
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime


class MonitorJobUpdate(BaseModel):
    """更新监控任务."""
    frequency: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|paused|error|archived)$")
    config_json: Optional[str] = None
    next_run_at: Optional[datetime] = None
