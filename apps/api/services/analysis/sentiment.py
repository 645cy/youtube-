"""Algorithm 3: 评论情感分析 — 关键词情绪词典法 (零 NLP 依赖).

被以下模块使用:
  - apps.api.routers.analysis           (sentiment_analysis endpoint)
  - apps.api.services.analysis_helpers  (fetch_video_comments + analyze)

设计决策:
  - 分词和评分逻辑委托给 SentimentTokenizer，便于独立测试和词典迭代.
  - 本类负责结果聚合 (SentimentResult / batch / aggregate).
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from .common import SentimentResult
from .sentiment_tokenizer import SentimentTokenizer, compound_score, score_percentages


class CommentSentimentAnalyzer:
    """评论情感分析器 — 关键词情绪词典法 (零 NLP 依赖).

    支持中英文混合, 表情符号识别, 否定词反转, 强度修饰符.
    Time: O(m * n), Space: O(1)
    """

    def __init__(self) -> None:
        self._tokenizer = SentimentTokenizer()

    def _neutral_result(self, comment_id: str, text: str) -> SentimentResult:
        return SentimentResult(
            comment_id=comment_id, text=text, compound_score=0.0,
            positive_score=0.0, negative_score=0.0, neutral_score=1.0,
            sentiment="neutral", key_positive_words=[], key_negative_words=[],
        )

    def analyze(self, comment_id: str, text: str) -> SentimentResult:
        """分析单条评论的情感.

        Args:
            comment_id: 评论唯一标识.
            text: 评论原文.

        Returns:
            SentimentResult 包含 compound_score、情感标签、关键词等.
        """
        if not text or not text.strip():
            return self._neutral_result(comment_id, text)

        tokens = self._tokenizer.tokenize(text)
        scores, pos_words, neg_words = self._tokenizer.score_tokens(tokens)
        compound = compound_score(scores)
        pos_pct, neg_pct, neu_pct = score_percentages(scores, compound)
        sentiment = "positive" if compound >= 0.05 else "negative" if compound <= -0.05 else "neutral"

        return SentimentResult(
            comment_id=comment_id, text=text[:200], compound_score=round(compound, 4),
            positive_score=round(pos_pct, 4), negative_score=round(neg_pct, 4),
            neutral_score=round(neu_pct, 4), sentiment=sentiment,
            key_positive_words=list(set(pos_words))[:10],
            key_negative_words=list(set(neg_words))[:10],
        )

    def batch_analyze(self, comments: list[tuple[str, str]]) -> list[SentimentResult]:
        """批量分析评论列表.

        Args:
            comments: [(comment_id, text), ...]

        Returns:
            SentimentResult 列表.
        """
        return [self.analyze(cid, text) for cid, text in comments]

    def aggregate(self, results: list[SentimentResult]) -> dict[str, Any]:
        """聚合多条评论的分析结果.

        Returns:
            包含 total_comments、positive_pct、negative_pct、neutral_pct、
            avg_compound、health_score 的字典.
        """
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
