"""Algorithm 7-8: 视频格式分析与缩略图 CTR 估算."""
from __future__ import annotations

import re
from typing import Any


class VideoFormatAnalyzer:
    """Algorithm 7: Shorts vs Long-form 爆款系数差异模型."""

    SHORTS_BENCHMARKS = {"views_per_sub": 5.0, "ctr": 8.5, "retention": 70.0, "half_life": 12}
    LONGFORM_BENCHMARKS = {"views_per_sub": 2.0, "ctr": 6.0, "retention": 50.0, "half_life": 24}

    @staticmethod
    def calculate_viral_coefficient(
        view_count: int, subscriber_count: int, is_short: bool,
        ctr: float | None = None, retention: float | None = None,
    ) -> dict[str, Any]:
        bench = VideoFormatAnalyzer.SHORTS_BENCHMARKS if is_short else VideoFormatAnalyzer.LONGFORM_BENCHMARKS
        vs_ratio = view_count / max(subscriber_count, 1)
        vs_score = min(100, vs_ratio / bench["views_per_sub"] * 50)
        ctr_score = min(100, (ctr or bench["ctr"]) / bench["ctr"] * 50) if ctr else 50
        ret_score = min(100, (retention or bench["retention"]) / bench["retention"] * 50) if retention else 50
        coefficient = (vs_score * 0.4 + ctr_score * 0.3 + ret_score * 0.3)
        return {
            "format": "shorts" if is_short else "long_form",
            "viral_coefficient": round(coefficient, 2),
            "views_per_subscriber": round(vs_ratio, 2),
            "vs_benchmark_score": round(vs_score, 2),
            "is_viral": coefficient >= 60,
            "half_life_hours": bench["half_life"],
        }


class ThumbnailCTREstimator:
    """Algorithm 8: 缩略图 CTR 启发式估算.

    基于标题和缩略图特征进行启发式评分 (无需实际 A/B 测试数据).
    """

    POWER_WORDS = {"惊人", "秘密", "免费", "立即", "独家", "终极", "必看",
                   "shocking", "secret", "free", "instant", "exclusive", "ultimate", "must"}
    CURiosity_TRIGGERS = {"为什么", "如何", "什么", "who", "what", "how", "why"}
    NEGATIVE_SIGNALS = {"测试", "草稿", "draft", "test", "private"}

    @staticmethod
    def estimate(title: str, has_face: bool = True, has_text: bool = True,
                 color_contrast: str = "high") -> dict[str, Any]:
        score = 50.0
        title_lower = title.lower()

        # 力量词加分
        pw_count = sum(1 for w in ThumbnailCTREstimator.POWER_WORDS if w in title_lower)
        score += pw_count * 5

        # 好奇心触发
        cq_count = sum(1 for w in ThumbnailCTREstimator.CURiosity_TRIGGERS if w in title_lower)
        score += cq_count * 4

        # 数字加分 (列表式标题)
        if re.search(r"\d+", title):
            score += 5

        # 长度优化 (40-60 字符最佳)
        tl = len(title)
        if 40 <= tl <= 60:
            score += 5
        elif tl > 80:
            score -= 10

        # 负面信号
        for neg in ThumbnailCTREstimator.NEGATIVE_SIGNALS:
            if neg in title_lower:
                score -= 15

        # 视觉元素
        if has_face:
            score += 8
        if has_text:
            score += 5
        if color_contrast == "high":
            score += 5

        score = max(0, min(100, score))

        ctr_estimate = 2.0 + score * 0.15  # 2% - 17% 范围
        return {
            "ctr_score": round(score, 2),
            "estimated_ctr_pct": round(ctr_estimate, 2),
            "has_face": has_face,
            "has_text_overlay": has_text,
            "color_contrast": color_contrast,
            "optimization_tips": ThumbnailCTREstimator._tips(score, tl),
        }

    @staticmethod
    def _tips(score: float, title_len: int) -> list[str]:
        tips = []
        if score < 60:
            tips.append("标题加入数字或力量词提升 CTR")
        if title_len < 30:
            tips.append("标题过短, 建议 40-60 字符")
        if title_len > 80:
            tips.append("标题过长, 建议精简到 60 字符以内")
        if score >= 70:
            tips.append("标题质量优秀, 保持当前风格")
        return tips
