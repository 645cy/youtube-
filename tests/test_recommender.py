"""Tests for recommender path matching."""
from __future__ import annotations

from apps.api.services.recommender import PathRecommender, UserProfile, load_default_paths


def test_load_default_paths_and_recommend_returns_ranked_output() -> None:
    profile = UserProfile(
        skills={"AI工具": 8, "内容创作": 7, "SEO优化": 6},
        has_camera=True,
        has_mic=True,
        editing_experience=6,
        weekly_hours=15,
        preferred_video_length="medium",
        can_show_face=False,
        monthly_budget_usd=100,
        willing_to_invest=True,
        interests=["AI", "视频创作", "被动收入"],
        native_language="zh",
        target_audience="global",
        has_computer=True,
        computer_os="windows",
        has_smartphone=True,
    )
    output = PathRecommender(load_default_paths()).recommend(profile, top_n=3)
    assert len(output.recommendations) == 3
    assert output.top_path is not None
    # CRG: Recommender should produce a usable workflow, not only scores.
    assert output.personalized_workflow is not None
