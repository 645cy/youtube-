"""Algorithm 9-10: 多频道聚合看板 KPI 与定时爬虫调度引擎."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


class DashboardKPICalculator:
    """Algorithm 9: 多频道聚合看板 KPI 计算."""

    @staticmethod
    def calculate(
        channels: list[dict[str, Any]],
        videos: list[dict[str, Any]],
        recent_analyses: list[dict[str, Any]],
    ) -> dict[str, Any]:
        total_channels = len(channels)
        total_videos = len(videos)
        total_views = sum(v.get("view_count", 0) or 0 for v in videos)
        total_subs = sum(c.get("subscriber_count", 0) or 0 for c in channels)
        viral_count = sum(1 for a in recent_analyses if a.get("score", 0) and a["score"] >= 3.0)
        evergreen_count = sum(
            1 for a in recent_analyses
            if a.get("analysis_type") == "evergreen" and a.get("score", 0) and a["score"] >= 60
        )
        sentiment_analyses = [
            a for a in recent_analyses if a.get("analysis_type") == "sentiment"
        ]
        avg_sentiment = (
            sum(a.get("score", 0) or 0 for a in sentiment_analyses)
            / max(1, len(sentiment_analyses))
        )

        # 找表现最好的频道
        top_channel = None
        if channels:
            top = max(channels, key=lambda c: c.get("view_count", 0) or 0)
            top_channel = top.get("title", "Unknown")

        return {
            "total_channels": total_channels,
            "total_videos": total_videos,
            "total_views": total_views,
            "total_subscribers": total_subs,
            "active_monitors": sum(1 for c in channels if c.get("has_active_monitor", False)),
            "recent_analyses": len(recent_analyses),
            "viral_videos_count": viral_count,
            "evergreen_videos_count": evergreen_count,
            "avg_sentiment_score": round(avg_sentiment, 2),
            "top_performing_channel": top_channel,
            "monetization_coverage_pct": round(
                sum(
                    1 for a in recent_analyses if a.get("analysis_type") == "monetization"
                )
                / max(1, total_videos) * 100,
                2,
            ),
        }


class SchedulerEngine:
    """Algorithm 10: 定时爬虫调度引擎.

    基于频道活跃度动态调整检测频率.
    """

    @staticmethod
    def calculate_next_run(
        last_run: datetime | None,
        base_interval_minutes: int,
        channel_upload_frequency: float,  # 每周上传数
    ) -> datetime:
        """计算下次运行时间.

        活跃度越高 -> 检测间隔越短.
        """
        import random
        now = datetime.now()

        # 根据上传频率调整间隔
        if channel_upload_frequency >= 7:  # 日更
            multiplier = 0.5
        elif channel_upload_frequency >= 3:  # 隔日更
            multiplier = 0.75
        elif channel_upload_frequency >= 1:  # 周更
            multiplier = 1.0
        else:
            multiplier = 2.0  # 月更 -> 降低检测频率

        interval = int(base_interval_minutes * multiplier)
        # 添加 10% 随机抖动, 避免精确时钟
        jitter = random.uniform(-interval * 0.1, interval * 0.1)
        next_run = (last_run or now) + timedelta(minutes=interval + jitter)
        return max(next_run, now + timedelta(minutes=5))
