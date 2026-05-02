"""Algorithm 2: 长尾 Evergreen 识别 — 高搜索低竞争检测."""
from __future__ import annotations

import math

from .common import EvergreenDetectionResult, KeywordMetrics


class LongTailEvergreenDetector:
    """长尾爆款(Evergreen)识别器 — 高搜索低竞争检测.

    核心公式:
      EPS = S_monthly / (C_density + 1) * 1/(Age+1) * A_score
      SSI = 1 - sigma/mu (搜索稳定性)

    Time: O(k + d), Space: O(1)
    """

    NICHE_BASELINE = {
        "gaming": 50000, "education": 15000, "tech": 30000,
        "finance": 12000, "entertainment": 80000, "lifestyle": 25000, "health": 20000,
    }

    def _norm_search(self, volume: int, niche: str) -> float:
        baseline = self.NICHE_BASELINE.get(niche.lower(), 30000)
        return min(100.0, max(0.0, (volume / baseline) * 50))

    def _calc_ssi(self, weekly: list[float]) -> float:
        if len(weekly) < 2:
            return 0.5
        mean = sum(weekly) / len(weekly)
        if mean <= 0:
            return 0.0
        var = sum((x - mean) ** 2 for x in weekly) / len(weekly)
        cv = math.sqrt(var) / mean
        return max(0.0, 1.0 - min(cv, 1.0))

    def detect(
        self,
        kw: KeywordMetrics,
        search_traffic_pct: float = 50.0,
        rewatch_rate: float = 0.3,
    ) -> EvergreenDetectionResult:
        search_norm = self._norm_search(kw.monthly_search_volume, kw.niche)
        ssi = self._calc_ssi(kw.weekly_search_history)
        competition = search_norm / (kw.competing_videos_count / 10 + 1)

        if kw.top_video_age_days < 365:
            aging = 1.0
        elif kw.top_video_age_days < 730:
            aging = 0.9
        elif kw.top_video_age_days < 1095:
            aging = 0.8
        else:
            aging = 0.7

        base_score = 0.30 * search_norm + 0.25 * (ssi * 100) + 0.25 * min(competition * 10, 100) + 0.20 * (aging * 100)
        rewatch_bonus = min(rewatch_rate * 50, 20)
        score = min(100.0, base_score + rewatch_bonus)

        if search_traffic_pct > 40:
            traffic = "search_driven"
        elif search_traffic_pct < 15:
            traffic = "browse_driven"
        else:
            traffic = "mixed"
        is_evergreen = score >= 60 and traffic in ("search_driven", "mixed") and rewatch_rate > 0.15

        recs = {"search_driven": "搜索驱动型Evergreen，优化SEO和标题关键词",
                "browse_driven": "推荐流量型，需提升互动率延长生命周期",
                "mixed": "均衡型流量，兼具搜索和推荐优势"}
        return EvergreenDetectionResult(
            is_evergreen=is_evergreen, evergreen_score=round(score, 2),
            search_stability_index=round(ssi, 4), competition_ratio=round(competition, 4),
            traffic_type=traffic, estimated_monthly_views=int(kw.monthly_search_volume * 0.1),
            recommendation=recs[traffic],
        )
