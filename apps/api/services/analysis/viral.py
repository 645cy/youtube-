"""Algorithm 1: 短期爆款检测 — View/Subscriber 比值衰减模型."""
from __future__ import annotations

import math
from datetime import timedelta

from .common import VideoMetrics, ViralDetectionResult


class ShortTermViralDetector:
    """短期爆款检测器 — View/Subscriber 比值衰减模型.

    核心公式:
      VRI(t) = (V_t / S) / (ln(S+1) * alpha_t)
      VS = w1*VRI + w2*VI + w3*CTR_norm + w4*R_norm

    Time: O(n), Space: O(1)
    """

    HALFLIFE = {"shorts": 12.0, "long_form": 24.0}
    WEIGHTS = {"vri": 0.35, "velocity": 0.25, "ctr": 0.20, "retention": 0.20}
    THRESHOLDS = [(20.0, "super"), (8.0, "big"), (3.0, "small"), (1.0, "potential"), (0.0, "none")]

    def _decay(self, hours: float, vtype: str) -> float:
        hl = self.HALFLIFE.get(vtype, 24.0)
        lam = math.log(2) / hl
        return math.exp(-lam * hours)

    def _calc_vri(self, m: VideoMetrics) -> float:
        if not m.views_history or m.channel_subscribers <= 0:
            return 0.0
        latest_time, latest_views = m.views_history[-1]
        hours = max(0.1, (latest_time - m.publish_time).total_seconds() / 3600)
        alpha = self._decay(hours, m.video_type)
        return (latest_views / m.channel_subscribers) / (math.log(m.channel_subscribers + 1) * alpha)

    def _calc_velocity(self, m: VideoMetrics, delta_h: float = 6.0) -> float:
        if len(m.views_history) < 2:
            return 0.0
        latest_time, latest_views = m.views_history[-1]
        cutoff = latest_time - timedelta(hours=delta_h)
        prev_views = m.views_history[0][1]
        for t, v in reversed(m.views_history[:-1]):
            if t <= cutoff:
                prev_views = v
                break
        time_diff = max(delta_h, (latest_time - m.publish_time).total_seconds() / 3600)
        return ((latest_views - prev_views) / max(prev_views, 1)) / (time_diff / delta_h)

    def detect(self, m: VideoMetrics) -> ViralDetectionResult:
        vri = self._calc_vri(m)
        velocity = self._calc_velocity(m)

        # CTR normalization
        ctr_norm = 0.5
        if m.ctr_history:
            baseline = 8.5 if m.video_type == "shorts" else 6.0
            ctr_norm = min(3.0, m.ctr_history[-1][1] / baseline)

        # Retention normalization
        ret_norm = 0.5
        if m.retention_history:
            baseline = 70.0 if m.video_type == "shorts" else 50.0
            ret_norm = min(2.0, m.retention_history[-1][1] / baseline)

        w = self.WEIGHTS
        score = (
            w["vri"] * max(0, vri)
            + w["velocity"] * max(0, velocity)
            + w["ctr"] * ctr_norm
            + w["retention"] * ret_norm
        )

        level = "none"
        for thr, lvl in self.THRESHOLDS:
            if score >= thr:
                level = lvl
                break

        is_viral = level in ("small", "big", "super")
        confidence = min(0.95, 0.3 + 0.1 * len(m.views_history))

        current_views = m.views_history[-1][1] if m.views_history else 0
        multiplier = 1 + math.log(score + 1) * 2 if score > 1.0 else 1.0
        peak = int(current_views * multiplier)

        recommendations = {
            "none": "继续监控，当前传播正常",
            "potential": "信号初显，建议增加互动推广",
            "small": "已进入推荐流，优化缩略图和标题",
            "big": "病毒传播中，准备后续内容承接流量",
            "super": "现象级传播，启动全渠道变现策略",
        }
        return ViralDetectionResult(
            is_viral=is_viral, viral_score=round(score, 4), viral_level=level,
            vri=round(vri, 4), velocity_index=round(velocity, 4),
            estimated_peak_views=peak, confidence=round(confidence, 4),
            recommendation=recommendations[level],
        )
