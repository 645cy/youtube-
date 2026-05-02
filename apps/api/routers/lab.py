"""
OCP 实验室 Router — 用户画像 + 变现路径推荐
路由前缀: /api/v1/lab

功能:
  - 用户画像提交与存储
  - 20 条变现路径匹配推荐
  - 个性化工作流生成
  - 路径详情查询
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query

from apps.api.schemas import (
    PathRecommendation,
    RecommendationResponse,
    UserProfile as UserProfileSchema,
)
from apps.api.services.recommender import (
    PathRecommender,
    UserProfile as RecommenderUserProfile,
    load_default_paths,
)

router = APIRouter(prefix="/lab", tags=["OCP Lab"])

# 全局推荐器实例 (预加载 20 条变现路径)
_recommender: PathRecommender | None = None


def _get_recommender() -> PathRecommender:
    """获取或创建推荐器实例 (懒加载)."""
    global _recommender
    if _recommender is None:
        paths = load_default_paths()
        _recommender = PathRecommender(paths=paths)
    return _recommender


def _convert_profile(schema_profile: UserProfileSchema) -> RecommenderUserProfile:
    """转换 Pydantic Schema -> 推荐器内部模型."""
    skills_dict = {s.name: s.level for s in schema_profile.skills} if schema_profile.skills else {}
    return RecommenderUserProfile(
        skills=skills_dict,
        has_camera=schema_profile.has_camera,
        has_mic=schema_profile.has_mic,
        editing_experience=schema_profile.editing_experience,
        weekly_hours=schema_profile.weekly_hours,
        preferred_video_length=schema_profile.preferred_video_length,
        can_show_face=schema_profile.can_show_face,
        monthly_budget_usd=schema_profile.monthly_budget_usd,
        willing_to_invest=schema_profile.willing_to_invest,
        interests=schema_profile.interests,
        native_language=schema_profile.native_language,
        target_audience=schema_profile.target_audience,
        has_computer=schema_profile.has_computer,
        computer_os=schema_profile.computer_os,
        has_smartphone=schema_profile.has_smartphone,
    )


@router.post("/profile", response_model=dict[str, Any])
async def submit_profile(
    profile: UserProfileSchema,
) -> dict[str, Any]:
    """提交用户画像, 返回画像摘要."""
    summary = {
        "skills": profile.skills,
        "weekly_hours": profile.weekly_hours,
        "monthly_budget_usd": profile.monthly_budget_usd,
        "interests": profile.interests,
        "can_show_face": profile.can_show_face,
        "has_camera": profile.has_camera,
        "has_computer": profile.has_computer,
        "difficulty_preference": _infer_difficulty(profile),
    }
    return {"status": "success", "profile_summary": summary}


def _infer_difficulty(profile: UserProfileSchema) -> str:
    """根据用户画像推断适合的难度级别."""
    avg_skill = 5.0
    if profile.skills:
        avg_skill = sum(s.level for s in profile.skills) / len(profile.skills)

    if avg_skill >= 7 and profile.weekly_hours >= 15:
        return "advanced"
    elif avg_skill >= 4 and profile.weekly_hours >= 8:
        return "intermediate"
    else:
        return "beginner"


@router.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(
    profile: UserProfileSchema,
    top_n: Annotated[int, Query(ge=1, le=20)] = 5,
    min_score: Annotated[float, Query(ge=0, le=100)] = 20.0,
) -> RecommendationResponse:
    """基于用户画像获取变现路径推荐.

    核心算法: 多因子加权匹配 (技能/时间/资金/兴趣/设备/人格/难度/ROI).
    """
    recommender = _get_recommender()
    user_profile = _convert_profile(profile)
    result = recommender.recommend(user_profile, top_n=top_n, min_score=min_score)

    recommendations = [
        PathRecommendation(
            path_id=r.path_id,
            path_name=r.path_name,
            path_name_en=r.path_name_en,
            match_score=r.match_score,
            match_reasons=r.match_reasons,
            estimated_startup_cost=r.estimated_startup_cost,
            estimated_monthly_income_low=r.estimated_monthly_income_low,
            estimated_monthly_income_high=r.estimated_monthly_income_high,
            time_to_first_income_months=r.time_to_first_income_months,
            difficulty=r.difficulty,
            required_tools=r.required_tools,
            workflow_steps=r.workflow_steps,
            pros=r.pros,
            cons=r.cons,
        )
        for r in result.recommendations
    ]

    top_path = recommendations[0] if recommendations else None

    return RecommendationResponse(
        user_profile_summary=result.user_profile_summary,
        recommendations=recommendations,
        top_path=top_path,
        personalized_workflow=result.personalized_workflow,
    )


@router.get("/paths", response_model=list[dict[str, Any]])
async def list_paths(
    category: Annotated[str | None, Query()] = None,
    difficulty: Annotated[str | None, Query(pattern="^(beginner|intermediate|advanced)$")] = None,
    min_income: Annotated[float | None, Query(ge=0)] = None,
) -> list[dict[str, Any]]:
    """获取所有变现路径列表 (支持筛选)."""
    recommender = _get_recommender()
    paths = recommender.paths

    result = []
    for p in paths:
        if category and p.category != category:
            continue
        if difficulty and p.difficulty != difficulty:
            continue
        if min_income and p.estimated_monthly_income_low_usd < min_income:
            continue
        result.append({
            "path_id": p.path_id,
            "path_name": p.path_name,
            "path_name_en": p.path_name_en,
            "category": p.category,
            "description": p.description,
            "difficulty": p.difficulty,
            "estimated_startup_cost_usd": p.estimated_startup_cost_usd,
            "estimated_monthly_income_low_usd": p.estimated_monthly_income_low_usd,
            "estimated_monthly_income_high_usd": p.estimated_monthly_income_high_usd,
            "time_to_first_income_months": p.time_to_first_income_months,
            "required_tools": p.required_tools,
            "workflow_steps": p.workflow_steps,
            "pros": p.pros,
            "cons": p.cons,
        })
    return result


@router.get("/paths/{path_id}", response_model=dict[str, Any])
async def get_path_detail(path_id: int) -> dict[str, Any]:
    """获取单条变现路径详情."""
    recommender = _get_recommender()
    for p in recommender.paths:
        if p.path_id == path_id:
            return {
                "path_id": p.path_id,
                "path_name": p.path_name,
                "path_name_en": p.path_name_en,
                "category": p.category,
                "description": p.description,
                "difficulty": p.difficulty,
                "estimated_startup_cost_usd": p.estimated_startup_cost_usd,
                "estimated_monthly_income_low_usd": p.estimated_monthly_income_low_usd,
                "estimated_monthly_income_high_usd": p.estimated_monthly_income_high_usd,
                "time_to_first_income_months": p.time_to_first_income_months,
                "required_skill_level": p.required_skill_level,
                "time_commitment_hours_per_week": p.time_commitment_hours_per_week,
                "face_required": p.face_required,
                "min_budget_usd": p.min_budget_usd,
                "relevant_skills": p.relevant_skills,
                "relevant_interests": p.relevant_interests,
                "required_tools": p.required_tools,
                "workflow_steps": p.workflow_steps,
                "pros": p.pros,
                "cons": p.cons,
            }
    raise HTTPException(status_code=404, detail=f"Path {path_id} not found")


@router.post("/quick-match")
async def quick_match(
    weekly_hours: Annotated[float, Query(ge=0, le=168)] = 10,
    monthly_budget: Annotated[float, Query(ge=0)] = 0,
    can_show_face: bool = True,
    has_computer: bool = True,
    interests: Annotated[list[str] | None, Query()] = None,
) -> dict[str, Any]:
    """快速匹配 — 简化的五维评估 (无需完整画像).

    适合首次使用的快速体验场景.
    """
    profile = RecommenderUserProfile(
        skills={"content_creation": 5, "editing": 4},
        has_camera=False,
        has_mic=False,
        editing_experience=4,
        weekly_hours=weekly_hours,
        preferred_video_length="medium",
        can_show_face=can_show_face,
        monthly_budget_usd=monthly_budget,
        willing_to_invest=monthly_budget > 0,
        interests=interests or ["general"],
        native_language="zh",
        target_audience="global",
        has_computer=has_computer,
        computer_os="windows",
        has_smartphone=True,
    )

    recommender = _get_recommender()
    result = recommender.recommend(profile, top_n=3, min_score=15.0)

    return {
        "quick_match": True,
        "recommendations": [
            {
                "path_id": r.path_id,
                "path_name": r.path_name,
                "match_score": r.match_score,
                "match_reasons": r.match_reasons,
                "difficulty": r.difficulty,
            }
            for r in result.recommendations
        ],
        "suggestion": "建议提交完整画像获取更精准的推荐" if len(result.recommendations) < 3 else None,
    }
