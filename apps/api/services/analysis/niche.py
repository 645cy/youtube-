"""Algorithm 5: Niche 评估打分卡 — 四维度几何平均."""
from __future__ import annotations

from .common import NicheMetrics, NicheScoringResult


class NicheScoringCard:
    """Niche 评估打分卡 — 四维度几何平均.

    NicheScore = (TP * MD * (1-AR) * RC)^0.25
    四维度: 流量潜力 / 变现密度 / (1-AI替代率) / 可复制性
    """

    THRESHOLDS = {"blue_ocean": 70.0, "viable": 50.0, "saturated": 30.0, "avoid": 0.0}

    def _traffic_potential(self, m: NicheMetrics) -> float:
        baseline = 50000
        search_score = min(100, (m.monthly_search_volume / baseline) * 50)
        growth = 50 + m.growth_trend_12m * 300 if m.growth_trend_12m >= 0 else max(0, 50 + m.growth_trend_12m * 200)
        growth = min(100, growth)
        evergreen = m.evergreen_content_ratio * 100
        return min(100, 0.40 * search_score + 0.35 * growth + 0.25 * evergreen)

    def _monetization_density(self, m: NicheMetrics) -> float:
        rpm_ratio = m.avg_rpm / max(m.max_rpm_in_niche, 1)
        rpm_score = rpm_ratio * 100
        if m.competing_channels_count < 100:
            comp_mult = 1.0
        elif m.competing_channels_count < 500:
            comp_mult = 0.85
        elif m.competing_channels_count < 2000:
            comp_mult = 0.65
        else:
            comp_mult = 0.45
        freq_mult = 1.0 if m.avg_video_upload_frequency <= 2 else 0.9 if m.avg_video_upload_frequency <= 4 else 0.75
        return min(100, rpm_score * comp_mult * freq_mult)

    def _ai_replaceability(self, m: NicheMetrics) -> float:
        ai_ratio = m.ai_content_detected_ratio
        script_diff = 1.0 - m.required_skill_level / 10.0
        pers_inv = 1.0 - m.personality_dependency
        return min(100, (ai_ratio * 0.30 + script_diff * 0.30 + pers_inv * 0.40) * 100)

    def _reproducibility(self, m: NicheMetrics) -> float:
        skill_match = min(1.0, m.creator_skill_level / max(m.required_skill_level, 1))
        resource = min(1.0, 5000 / max(m.startup_cost_estimate, 100))
        videos_pw = m.weekly_time_available / max(m.estimated_production_hours, 1)
        time_feas = min(1.0, videos_pw / 2.0)
        passion = m.passion_score / 10.0
        return min(100, (skill_match * 0.30 + resource * 0.20 + time_feas * 0.25 + passion * 0.25) * 100)

    def score(self, m: NicheMetrics) -> NicheScoringResult:
        tp = self._traffic_potential(m)
        md = self._monetization_density(m)
        ar = self._ai_replaceability(m)
        rc = self._reproducibility(m)

        ar_inv = max(0.01, 1.0 - ar / 100.0)
        total = (tp / 100 * md / 100 * ar_inv * rc / 100) ** 0.25 * 100

        opportunity = "avoid"
        for level, threshold in sorted(self.THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if total >= threshold:
                opportunity = level
                break

        swot = self._swot(tp, md, ar, rc, m)
        recs = {"blue_ocean": "强烈推荐进入！该Niche处于蓝海。",
                "viable": "值得尝试，但需要明确定位差异化策略。",
                "saturated": "竞争激烈，建议寻找细分子领域切入。",
                "avoid": "不建议进入，可考虑关联但更细分的领域。"}

        return NicheScoringResult(
            niche_name=m.niche_name, total_score=round(total, 2),
            traffic_potential=round(tp, 2), monetization_density=round(md, 2),
            ai_replaceability=round(ar, 2), reproducibility=round(rc, 2),
            opportunity_level=opportunity, swot_summary=swot, recommendation=recs[opportunity],
        )

    def compare(self, niches: list[NicheMetrics]) -> list[NicheScoringResult]:
        results = [self.score(n) for n in niches]
        return sorted(results, key=lambda x: x.total_score, reverse=True)

    def _swot(self, tp: float, md: float, ar: float, rc: float, m: NicheMetrics) -> dict[str, list[str]]:
        s, w, o, t = [], [], [], []
        if tp > 70:
            s.append(f"高流量潜力 (TP={tp:.1f})")
        if md > 60:
            s.append(f"良好变现能力 (MD={md:.1f})")
        if rc > 70:
            s.append(f"高个人可复制性 (RC={rc:.1f})")
        if m.growth_trend_12m > 0.1:
            s.append(f"快速增长趋势 (+{m.growth_trend_12m*100:.0f}%)")
        if tp < 40:
            w.append(f"流量潜力有限 (TP={tp:.1f})")
        if rc < 40:
            w.append(f"个人可复制性低 (RC={rc:.1f})")
        if ar < 40:
            o.append("AI替代率低，人格化壁垒高")
        if m.evergreen_content_ratio > 0.6:
            o.append("高Evergreen比例，长尾收益可期")
        if m.competing_channels_count < 200:
            o.append(f"竞争频道少 ({m.competing_channels_count})")
        if ar > 70:
            t.append(f"AI替代风险高 (AR={ar:.1f})")
        if m.competing_channels_count > 1000:
            t.append(f"竞争激烈 ({m.competing_channels_count}+频道)")
        return {"strengths": s, "weaknesses": w, "opportunities": o, "threats": t}
