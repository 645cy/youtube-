"""OCP Lab (User Profile + Recommendation) Pydantic Schemas."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from apps.api.config import settings


class UserSkill(BaseModel):
    """用户技能项."""
    name: str
    level: int = Field(1, ge=1, le=10)


class UserProfile(BaseModel):
    """OCP 实验室用户画像."""
    skills: list[UserSkill] = []
    has_camera: bool = False
    has_mic: bool = False
    editing_experience: int = Field(0, ge=0, le=10)
    weekly_hours: float = Field(10, ge=0, le=168)
    preferred_video_length: str = "medium"
    can_show_face: bool = True
    monthly_budget_usd: float = Field(0, ge=0)
    willing_to_invest: bool = False
    interests: list[str] = []
    native_language: str = "zh"
    target_audience: str = settings.DEFAULT_TARGET_REGION
    has_computer: bool = True
    computer_os: str = "windows"
    has_smartphone: bool = True


class PathRecommendation(BaseModel):
    """单条变现路径推荐结果."""
    path_id: int
    path_name: str
    path_name_en: str
    match_score: float
    match_reasons: list[str]
    estimated_startup_cost: float
    estimated_monthly_income_low: float
    estimated_monthly_income_high: float
    time_to_first_income_months: int
    difficulty: str
    required_tools: list[str]
    workflow_steps: list[str]
    pros: list[str]
    cons: list[str]


class RecommendationResponse(BaseModel):
    """推荐响应."""
    user_profile_summary: dict[str, Any]
    recommendations: list[PathRecommendation]
    top_path: Optional[PathRecommendation] = None
    personalized_workflow: Optional[dict[str, Any]] = None
