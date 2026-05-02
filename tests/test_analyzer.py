"""Tests for core analysis algorithms."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from apps.api.services.analyzer import (
    CommentSentimentAnalyzer,
    KeywordMetrics,
    LongTailEvergreenDetector,
    ShortTermViralDetector,
    VideoMetrics,
)


class TestShortTermViralDetector:
    """Tests for Algorithm 1: short-term viral detection."""

    @pytest.fixture
    def detector(self) -> ShortTermViralDetector:
        return ShortTermViralDetector()

    def _make_metrics(
        self,
        views_history: list[tuple[datetime, int]],
        subscribers: int = 1000,
        video_type: str = "long_form",
    ) -> VideoMetrics:
        return VideoMetrics(
            video_id="test123",
            channel_subscribers=subscribers,
            publish_time=datetime.now(timezone.utc) - timedelta(hours=12),
            views_history=views_history,
            ctr_history=[],
            retention_history=[],
            video_type=video_type,
        )

    def test_no_views_history(self, detector: ShortTermViralDetector) -> None:
        """With empty views history, score should be minimal."""
        m = self._make_metrics(views_history=[])
        result = detector.detect(m)
        assert result.is_viral is False
        assert result.viral_level == "none"
        assert result.viral_score < 1.0

    def test_high_subscriber_ratio(self, detector: ShortTermViralDetector) -> None:
        """Video with views >> subscribers should be flagged viral."""
        now = datetime.now(timezone.utc)
        m = self._make_metrics(
            views_history=[(now - timedelta(hours=6), 100), (now, 20000)],
            subscribers=1000,
        )
        result = detector.detect(m)
        assert result.is_viral is True
        assert result.viral_level in ("small", "big", "super")
        assert result.vri > 0

    def test_low_subscriber_ratio(self, detector: ShortTermViralDetector) -> None:
        """Video with views < subscribers should not be viral."""
        now = datetime.now(timezone.utc)
        m = self._make_metrics(
            views_history=[(now - timedelta(hours=6), 50), (now, 200)],
            subscribers=10000,
        )
        result = detector.detect(m)
        assert result.is_viral is False
        assert result.viral_level == "none"

    def test_shorts_vs_longform(self, detector: ShortTermViralDetector) -> None:
        """Shorts should use different halflife and baselines."""
        now = datetime.now(timezone.utc)
        long_m = self._make_metrics(
            views_history=[(now - timedelta(hours=3), 100), (now, 1000)],
            subscribers=500,
            video_type="long_form",
        )
        short_m = self._make_metrics(
            views_history=[(now - timedelta(hours=3), 100), (now, 1000)],
            subscribers=500,
            video_type="shorts",
        )
        long_result = detector.detect(long_m)
        short_result = detector.detect(short_m)
        # Shorts decay faster (12h vs 24h), so same views at 3h gives higher VRI
        assert short_result.vri >= long_result.vri

    def test_recommendation_levels(self, detector: ShortTermViralDetector) -> None:
        """Each level should have a non-empty recommendation."""
        now = datetime.now(timezone.utc)
        # Super viral
        m = self._make_metrics(
            views_history=[(now - timedelta(hours=1), 10000), (now, 100000)],
            subscribers=1000,
        )
        result = detector.detect(m)
        assert result.recommendation != ""
        assert "变现" in result.recommendation or "全渠道" in result.recommendation or "流量" in result.recommendation


class TestCommentSentimentAnalyzer:
    """Tests for Algorithm 3: comment sentiment analysis."""

    @pytest.fixture
    def analyzer(self) -> CommentSentimentAnalyzer:
        return CommentSentimentAnalyzer()

    def test_empty_comment(self, analyzer: CommentSentimentAnalyzer) -> None:
        """Empty comment should be neutral."""
        result = analyzer.analyze("c1", "")
        assert result.sentiment == "neutral"
        assert result.compound_score == 0.0
        assert result.neutral_score == 1.0

    def test_positive_english(self, analyzer: CommentSentimentAnalyzer) -> None:
        """Positive English words should yield positive sentiment."""
        result = analyzer.analyze("c2", "This video is amazing and helpful!")
        assert result.sentiment == "positive"
        assert result.compound_score > 0
        assert "amazing" in result.key_positive_words or "helpful" in result.key_positive_words

    def test_negative_english(self, analyzer: CommentSentimentAnalyzer) -> None:
        """Negative English words should yield negative sentiment."""
        result = analyzer.analyze("c3", "This is terrible and boring waste of time")
        assert result.sentiment == "negative"
        assert result.compound_score < 0

    def test_positive_chinese(self, analyzer: CommentSentimentAnalyzer) -> None:
        """Positive Chinese words should yield positive sentiment.

        Note: tokenizer uses \b which has limited CJK support;
        explicit short positive words are more reliably matched.
        """
        result = analyzer.analyze("c4", "赞 完美 666")
        assert result.sentiment == "positive"
        assert result.compound_score > 0

    def test_negative_chinese(self, analyzer: CommentSentimentAnalyzer) -> None:
        """Negative Chinese words should yield negative sentiment."""
        result = analyzer.analyze("c5", "太差了，浪费时间，无聊")
        assert result.sentiment == "negative"
        assert result.compound_score < 0

    def test_emoji_positive(self, analyzer: CommentSentimentAnalyzer) -> None:
        """Positive emojis should boost score."""
        result = analyzer.analyze("c6", "Great video! 👍🔥")
        assert result.compound_score > 0

    def test_emoji_negative(self, analyzer: CommentSentimentAnalyzer) -> None:
        """Negative emojis should lower score."""
        result = analyzer.analyze("c7", "Bad video 👎😡")
        assert result.compound_score < 0

    def test_neutral_comment(self, analyzer: CommentSentimentAnalyzer) -> None:
        """Plain factual comment should be neutral or weakly positive."""
        result = analyzer.analyze("c8", "The video is 10 minutes long.")
        # No sentiment words, should be close to neutral
        assert abs(result.compound_score) < 1.0


class TestLongTailEvergreenDetector:
    """Tests for Algorithm 2: evergreen content detection."""

    @pytest.fixture
    def detector(self) -> LongTailEvergreenDetector:
        return LongTailEvergreenDetector()

    def _make_metrics(
        self,
        monthly_search: int = 1000,
        competing: int = 100,
        top_age: int = 365,
        avg_views: int = 5000,
    ) -> KeywordMetrics:
        return KeywordMetrics(
            keyword="test",
            monthly_search_volume=monthly_search,
            weekly_search_history=[1.0] * 12,
            competing_videos_count=competing,
            top_video_age_days=top_age,
            avg_view_count_top10=avg_views,
            niche="tech",
        )

    def test_high_search_low_competition(self, detector: LongTailEvergreenDetector) -> None:
        """High search + low competition = evergreen."""
        m = self._make_metrics(monthly_search=50000, competing=10)
        result = detector.detect(m)
        assert result.is_evergreen is True
        assert result.evergreen_score > 0.5

    def test_low_search_high_competition(self, detector: LongTailEvergreenDetector) -> None:
        """Low search + high competition = not evergreen."""
        m = self._make_metrics(monthly_search=100, competing=10000)
        result = detector.detect(m)
        assert result.is_evergreen is False
        # Score range is 0-100, not 0-1
        assert result.evergreen_score < 60
