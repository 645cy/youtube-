"""Tests for apps.api.services.analysis.sentiment_tokenizer."""
from __future__ import annotations

import pytest

from apps.api.services.analysis.sentiment_tokenizer import (
    SentimentTokenizer,
    compound_score,
    score_percentages,
)


class TestSentimentTokenizerTokenize:
    def test_tokenizes_english(self) -> None:
        tokenizer = SentimentTokenizer()
        tokens = tokenizer.tokenize("good video amazing content")
        assert "good" in tokens
        assert "video" in tokens
        assert "amazing" in tokens

    def test_tokenizes_chinese(self) -> None:
        tokenizer = SentimentTokenizer()
        tokens = tokenizer.tokenize("喜欢感谢有用")
        # 注意: \b 对中文字符的边界行为是将连续中文字符整体匹配
        assert "喜欢感谢有用" in tokens

    def test_tokenizes_chinese_mixed_with_english(self) -> None:
        tokenizer = SentimentTokenizer()
        tokens = tokenizer.tokenize("good 喜欢 thanks")
        assert "good" in tokens
        assert "喜欢" in tokens

    def test_extracts_emojis(self) -> None:
        tokenizer = SentimentTokenizer()
        tokens = tokenizer.tokenize("good 👍 amazing ❤️")
        assert "👍" in tokens
        # 注意: "❤️" 是组合字符 (❤ + 变体选择器), 正则将其分开匹配
        assert "❤" in tokens


class TestSentimentTokenizerScoreToken:
    def test_scores_positive_word(self) -> None:
        tokenizer = SentimentTokenizer()
        result = tokenizer.score_token(["good"], 0)
        assert result is not None
        assert result.final > 0
        assert result.negated is False

    def test_scores_negative_word(self) -> None:
        tokenizer = SentimentTokenizer()
        result = tokenizer.score_token(["bad"], 0)
        assert result is not None
        assert result.final < 0

    def test_scores_emoji(self) -> None:
        tokenizer = SentimentTokenizer()
        result = tokenizer.score_token(["👍"], 0)
        assert result is not None
        assert result.final > 0

    def test_negation_flips_score(self) -> None:
        tokenizer = SentimentTokenizer()
        result = tokenizer.score_token(["not", "good"], 1)
        assert result is not None
        assert result.final < 0  # negated positive becomes negative
        assert result.negated is True

    def test_intensifier_boosts_score(self) -> None:
        tokenizer = SentimentTokenizer()
        result = tokenizer.score_token(["very", "good"], 1)
        assert result is not None
        assert result.final > 1.0  # boosted by intensifier

    def test_returns_none_for_neutral(self) -> None:
        tokenizer = SentimentTokenizer()
        assert tokenizer.score_token(["the"], 0) is None


class TestCompoundScore:
    def test_empty_returns_zero(self) -> None:
        assert compound_score([]) == 0.0

    def test_positive_scores_positive(self) -> None:
        score = compound_score([1.0, 1.5, 2.0])
        assert score > 0
        assert -1.0 <= score <= 1.0

    def test_negative_scores_negative(self) -> None:
        score = compound_score([-1.0, -1.5])
        assert score < 0
        assert -1.0 <= score <= 1.0

    def test_clamps_to_bounds(self) -> None:
        # Extreme values should still be within [-1, 1]
        score = compound_score([100.0, 100.0])
        assert score <= 1.0


class TestScorePercentages:
    def test_positive_dominant(self) -> None:
        pos, neg, neu = score_percentages([1.0, 0.5], 0.5)
        assert pos > neg
        assert pos + neg + neu == pytest.approx(1.0, abs=0.01)

    def test_all_neutral_when_no_scores(self) -> None:
        pos, neg, neu = score_percentages([], 0.0)
        assert pos == 0.0
        assert neg == 0.0
        assert neu == 1.0

    def test_negative_dominant(self) -> None:
        pos, neg, neu = score_percentages([-1.0, -0.5], -0.5)
        assert neg > pos


class TestEndToEnd:
    """端到端测试：模拟 CommentSentimentAnalyzer 的核心流程."""

    def test_positive_comment(self) -> None:
        tokenizer = SentimentTokenizer()
        tokens = tokenizer.tokenize("This is a great and helpful video, thanks!")
        scores, pos_words, neg_words = tokenizer.score_tokens(tokens)
        compound = compound_score(scores)
        assert compound > 0
        assert len(pos_words) > 0

    def test_negative_comment(self) -> None:
        tokenizer = SentimentTokenizer()
        tokens = tokenizer.tokenize("This video is bad and boring, waste of time")
        scores, pos_words, neg_words = tokenizer.score_tokens(tokens)
        compound = compound_score(scores)
        assert compound < 0
        assert len(neg_words) > 0

    def test_mixed_with_negation(self) -> None:
        tokenizer = SentimentTokenizer()
        tokens = tokenizer.tokenize("not bad actually pretty good")
        scores, pos_words, neg_words = tokenizer.score_tokens(tokens)
        # "not bad" should be scored as positive (negation flips "bad")
        assert any("bad(negated)" in w for w in pos_words)
