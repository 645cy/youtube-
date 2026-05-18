"""Algorithm 4: 视频变现信号检测 — 联盟链接/赞助话术/优惠码."""
from __future__ import annotations

import re
from typing import Any

from .common import MonetizationResult


class MonetizationSignalDetector:
    """视频变现信号检测器 — 基于 Princeton AdIntuition 研究.

    检测信号:
      - 联盟链接模式 (Amazon/ShareASale 等)
      - UTM 追踪参数
      - 优惠码模式
      - 赞助披露话术
      - 商品/课程/会员链接
    """

    AFFILIATE_DOMAINS = {"amazon", "amzn", "amzn.to", "shareasale", "cj.com",
                         "clickbank", "impact.com", "rakuten", "awin", "gumroad"}
    UTM_KEYS = ["utm_source", "utm_medium", "utm_campaign", "aff_id", "ref", "tag"]
    COUPON_PATTERNS = [
        r"(?:code|coupon|promo)\s*[:：]\s*([A-Z0-9]{4,15})",
        r'(?:use|enter)\s+(?:code|coupon|promo)\s+["\']?([A-Z0-9]{4,15})["\']?',
        # CRG: Avoid treating the literal word "code" as the coupon in "use code SAVE20".
        r'(?:use|enter)\s+(?!code\b|coupon\b|promo\b)["\']?([A-Z0-9]{4,15})["\']?',
    ]
    SPONSOR_PHRASES = ["sponsored by", "paid promotion", "partnered with",
                       "thanks to", "this video is sponsored", "#sponsored", "#ad",
                       "赞助", "合作", "付费推广", "本视频由"]
    CTA_PHRASES = ["link in description", "use my code", "use my link",
                   "i earn a small commission", "affiliate link", "full disclosure",
                   "购买链接", "链接在描述", "使用我的链接", "佣金"]

    def _extract_urls(self, text: str) -> list[str]:
        return re.findall(r'https?://[^\s<>"\'\`\)\]\}]+', text)

    def _check_affiliate(self, url: str) -> dict[str, Any]:
        result = {"url": url, "is_affiliate": False, "confidence": 0.0, "signals": []}
        parsed = url.lower()
        for domain in self.AFFILIATE_DOMAINS:
            if domain in parsed:
                result["is_affiliate"] = True
                result["confidence"] += 0.35
                result["signals"].append(f"domain:{domain}")
                break
        for key in self.UTM_KEYS:
            if key in parsed:
                result["confidence"] += 0.25
                result["signals"].append(f"utm:{key}")
        shorteners = ["bit.ly", "t.co", "tinyurl", "goo.gl", "yt.be"]
        if any(s in parsed for s in shorteners):
            result["confidence"] += 0.15
        result["confidence"] = min(1.0, result["confidence"])
        return result

    def _detect_coupons(self, text: str) -> list[str]:
        coupons = []
        for pat in self.COUPON_PATTERNS:
            coupons.extend(re.findall(pat, text, re.IGNORECASE))
        seen = set()
        unique = []
        for c in coupons:
            c = c.upper().strip()
            if c not in seen and len(c) >= 4:
                seen.add(c)
                unique.append(c)
        return unique[:5]

    def detect(self, video_id: str, title: str, description: str,
               transcript: str = "") -> MonetizationResult:
        full = f"{title} {description} {transcript}"
        urls = self._extract_urls(full)
        link_results = [self._check_affiliate(u) for u in urls]
        aff_links = [r for r in link_results if r["is_affiliate"]]
        aff_conf = max((r["confidence"] for r in aff_links), default=0.0)
        coupons = self._detect_coupons(description)
        if coupons:
            aff_conf = min(1.0, aff_conf + 0.15)

        full_lower = full.lower()
        has_sponsor = any(p in full_lower for p in self.SPONSOR_PHRASES)
        cta_count = sum(full_lower.count(p) for p in self.CTA_PHRASES)
        sponsor_score = (0.6 if has_sponsor else 0) + min(0.4, cta_count * 0.1)

        # 其他变现类型
        merch = any(kw in full_lower for kw in ["merch", "teespring", "shopify", "store."])
        course = any(kw in full_lower for kw in ["udemy", "coursera", "skillshare", "teachable", "course"])
        membership = any(kw in full_lower for kw in ["patreon", "membership", "join", "subscribe"])

        types = []
        if aff_links:
            types.append("affiliate")
        if sponsor_score > 0.3:
            types.append("sponsorship")
        if merch:
            types.append("merch")
        if course:
            types.append("course")
        if membership:
            types.append("membership")

        ms = max(aff_conf * 100, sponsor_score * 100)
        ms += sum([10 for b in [merch, course, membership] if b])
        ms = min(100.0, ms)

        if aff_links and has_sponsor:
            disclosure = "compliant"
        elif aff_links and not has_sponsor:
            disclosure = "missing"
        else:
            disclosure = "partial"

        tier = "high" if ms >= 60 else "medium" if ms >= 30 else "low"

        return MonetizationResult(
            video_id=video_id, is_monetized=ms >= 20.0,
            monetization_score=round(ms, 2), affiliate_detected=len(aff_links) > 0,
            affiliate_confidence=round(aff_conf, 4),
            sponsorship_detected=sponsor_score > 0.3,
            sponsorship_score=round(sponsor_score, 4),
            detected_coupons=coupons, monetization_types=types,
            disclosure_compliance=disclosure, estimated_monthly_revenue_tier=tier,
        )
