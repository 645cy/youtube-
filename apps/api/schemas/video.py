"""Video Pydantic Schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class VideoCreate(BaseModel):
    """创建视频记录请求."""
    youtube_id: str = Field(..., min_length=11, max_length=11)
    channel_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    published_at: Optional[datetime] = None
    duration: Optional[int] = Field(None, ge=0)
    view_count: Optional[int] = Field(None, ge=0)
    like_count: Optional[int] = Field(None, ge=0)
    comment_count: Optional[int] = Field(None, ge=0)
    thumbnail_url: Optional[str] = None
    tags: Optional[list[str]] = None
    category_id: Optional[str] = None
    language: Optional[str] = None
    is_short: bool = False


class VideoRead(BaseModel):
    """视频响应."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    youtube_id: str
    channel_id: int
    title: str
    description: Optional[str] = None
    published_at: Optional[datetime] = None
    duration: Optional[int] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    thumbnail_url: Optional[str] = None
    tags: Optional[str] = None
    category_id: Optional[str] = None
    language: Optional[str] = None
    is_short: bool
    created_at: datetime


class VideoList(BaseModel):
    """视频列表响应."""
    items: list[VideoRead]
    total: int
    offset: int
    limit: int


class VideoFilter(BaseModel):
    """视频筛选参数."""
    channel_id: Optional[int] = None
    is_short: Optional[bool] = None
    category_id: Optional[str] = None
    language: Optional[str] = None
    min_views: Optional[int] = None
    min_duration: Optional[int] = None
    max_duration: Optional[int] = None
    sort_by: str = "published_at"
    sort_order: str = "desc"
    offset: int = 0
    limit: int = 50
