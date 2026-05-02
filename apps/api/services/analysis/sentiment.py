"""Algorithm 3: 评论情感分析 — 关键词情绪词典法 (零 NLP 依赖)."""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from .common import SentimentResult


class CommentSentimentAnalyzer:
    """评论情感分析器 — 关键词情绪词典法 (零 NLP 依赖).

    支持中英文混合, 表情符号识别, 否定词反转, 强度修饰符.
    Time: O(m * n), Space: O(1)
    """

    POS_WORDS = {
        "good", "great", "amazing", "awesome", "excellent", "fantastic", "wonderful",
        "love", "like", "enjoy", "best", "perfect", "brilliant", "outstanding",
        "superb", "incredible", "helpful", "useful", "informative", "clear",
        "easy", "well", "nice", "beautiful", "cool", "fun", "funny", "entertaining",
        "impressive", "inspiring", "thanks", "thank", "appreciate", "recommended",
        "quality", "professional", "insightful", "valuable", "educational", "learned",
        "subscribed", "follow", "fan", "masterpiece", "must_watch",
        "喜欢", "感谢", "有用", "棒", "好", "赞", "优秀", "清晰", "精彩", "好看",
        "学到了", "收藏", "支持", "加油", "顶", "厉害", "强", "牛", "给力", "完美",
        "不错", "哇", "666", "yyds", "订阅",
    }

    NEG_WORDS = {
        "bad", "terrible", "awful", "horrible", "hate", "dislike", "worst",
        "boring", "waste", "useless", "stupid", "ridiculous", "annoying",
        "disappointing", "poor", "weak", "wrong", "misleading", "clickbait",
        "fake", "false", "incorrect", "confusing", "difficult", "hard",
        "slow", "spam", "scam", "trash", "garbage", "suck", "sucks",
        "hated", "wasted", "frustrated", "frustrating", "pointless",
        "overrated", "not_helpful", "delete",
        "垃圾", "差", "烂", "讨厌", "无聊", "浪费", "失望", "误导", "假",
        "骗人", "难听", "难看", "退货", "取消订阅", "踩", "举报", "错误",
        "不好", "没有用", "浪费时间", "恶心", "糟糕", "无语",
    }

    NEGATION = {"not", "no", "never", "neither", "nor", "n't", "without",
                "hardly", "barely", "dont", "doesnt", "didnt", "wasnt", "isnt",
                "不是", "没有", "别", "不太", "不怎么", "但", "但是", "不过"}

    INTENSIFIERS = {"very", "extremely", "incredibly", "absolutely", "really", "so",
                    "super", "非常", "特别", "极其", "超级", "太", "很", "十分", "真的"}

    EMOJI = {
        "❤": 2.0, "❤️": 2.0, "👍": 1.5, "😍": 2.0, "😊": 1.5, "😁": 1.5,
        "👏": 1.5, "🙌": 1.5, "🔥": 1.5, "💯": 1.5, "😂": 1.0, "✨": 1.0,
        "😎": 1.0, "🥰": 2.0, "🤩": 2.0, "😀": 1.5, "👌": 1.0, "✅": 1.0,
        "💪": 1.0, "🎉": 1.5, "🙏": 1.0, "⭐": 1.0, "🌟": 1.5, "💖": 2.0,
        "👎": -1.5, "😠": -1.5, "😡": -2.0, "😤": -1.5, "😒": -1.0,
        "😢": -1.0, "😭": -1.0, "🤬": -2.0, "💔": -2.0, "😞": -1.5,
        "🙄": -0.5, "🤮": -2.0, "🤢": -1.5, "😐": -0.3, "😑": -0.3, "😕": -0.5,
    }

    def __init__(self) -> None:
        self._pos = {w.lower() for w in self.POS_WORDS}
        self._neg = {w.lower() for w in self.NEG_WORDS}
        self._negation = {w.lower() for w in self.NEGATION}
        self._intens = {w.lower() for w in self.INTENSIFIERS}

    def _tokenize(self, text: str) -> list[str]:
        words = re.findall(r"\b[a-zA-Z\u4e00-\u9fff]+\b", text.lower())
        emojis = re.findall(
            r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
            r"\U0001F680-\U0001F6FF\U00002702-\U000027B0"
            r"\U000024C2-\U0001F251\u2764\u2b50\u2728]", text
        )
        return words + emojis

    def analyze(self, comment_id: str, text: str) -> SentimentResult:
        if not text or not text.strip():
            return SentimentResult(
                comment_id=comment_id, text=text, compound_score=0.0,
                positive_score=0.0, negative_score=0.0, neutral_score=1.0,
                sentiment="neutral", key_positive_words=[], key_negative_words=[],
            )

        tokens = self._tokenize(text)
        scores: list[float] = []
        pos_words, neg_words = [], []

        for i, token in enumerate(tokens):
            if len(token) == 1 and ord(token) > 127:
                if token in self.EMOJI:
                    scores.append(self.EMOJI[token])
                continue

            is_pos = token in self._pos
            is_neg = token in self._neg
            if not is_pos and not is_neg:
                continue

            base = 1.0 if is_pos else -1.0
            modifier = 1.0
            negated = False

            if i > 0:
                prev = tokens[i - 1]
                if prev in self._negation:
                    negated = True
                    modifier *= -1.0
                elif prev in self._intens:
                    modifier *= 1.5

            final = base * modifier * (1.3 if token.isupper() and len(token) > 1 else 1.0)
            scores.append(final)

            if final > 0:
                pos_words.append(f"{token}(negated)" if negated else token)
            elif final < 0:
                neg_words.append(f"{token}(negated)" if negated else token)

        if scores:
            compound = sum(scores) / math.sqrt(sum(abs(s) for s in scores) ** 2 + 15)
            compound = max(-1.0, min(1.0, compound))
        else:
            compound = 0.0

        pos_sum = sum(max(0, s) for s in scores)
        neg_sum = sum(max(0, -s) for s in scores)
        total = pos_sum + neg_sum

        if total > 0:
            pos_pct = pos_sum / total * abs(compound) if compound > 0 else 0
            neg_pct = neg_sum / total * abs(compound) if compound < 0 else 0
            neu_pct = 1.0 - abs(compound)
        else:
            pos_pct = neg_pct = 0.0
            neu_pct = 1.0

        sentiment = "positive" if compound >= 0.05 else "negative" if compound <= -0.05 else "neutral"

        return SentimentResult(
            comment_id=comment_id, text=text[:200], compound_score=round(compound, 4),
            positive_score=round(pos_pct, 4), negative_score=round(neg_pct, 4),
            neutral_score=round(neu_pct, 4), sentiment=sentiment,
            key_positive_words=list(set(pos_words))[:10],
            key_negative_words=list(set(neg_words))[:10],
        )

    def batch_analyze(self, comments: list[tuple[str, str]]) -> list[SentimentResult]:
        return [self.analyze(cid, text) for cid, text in comments]

    def aggregate(self, results: list[SentimentResult]) -> dict[str, Any]:
        total = len(results)
        if total == 0:
            return {"total_comments": 0}
        sentiments = Counter(r.sentiment for r in results)
        avg_compound = sum(r.compound_score for r in results) / total
        health = min(100, max(0, 50 + avg_compound * 50))
        return {
            "total_comments": total,
            "positive_pct": round(sentiments.get("positive", 0) / total * 100, 2),
            "negative_pct": round(sentiments.get("negative", 0) / total * 100, 2),
            "neutral_pct": round(sentiments.get("neutral", 0) / total * 100, 2),
            "avg_compound": round(avg_compound, 4),
            "health_score": round(health, 2),
        }
