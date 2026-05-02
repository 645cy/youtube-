"""Channel Pydantic Schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ChannelCreate(BaseModel):
    """创建频道请求."""
    youtube_id: str = Field(..., min_length=5, max_length=24)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    subscriber_count: Optional[int] = Field(None, ge=0)
    video_count: Optional[int] = Field(None, ge=0)
    view_count: Optional[int] = Field(None, ge=0)
    thumbnail_url: Optional[str] = None
    country: Optional[str] = Field(None, max_length=2)
    language: Optional[str] = Field(None, max_length=5)
    niche: Optional[str] = Field(None, max_length=50)


class ChannelRead(BaseModel):
    """频道响应 (含关联视频数)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    youtube_id: str
    title: str
    description: Optional[str] = None
    subscriber_count: Optional[int] = None
    video_count: Optional[int] = None
    view_count: Optional[int] = None
    thumbnail_url: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    niche: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ChannelUpdate(BaseModel):
    """更新频道请求 (全字段可选)."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    subscriber_count: Optional[int] = None
    video_count: Optional[int] = None
    view_count: Optional[int] = None
    thumbnail_url: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    niche: Optional[str] = None


class ChannelList(BaseModel):
    """频道列表响应."""
    items: list[ChannelRead]
    total: int
    offset: int
    limit: int
