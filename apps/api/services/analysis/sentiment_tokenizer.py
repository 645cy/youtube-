"""
评论情感分析的分词与评分引擎 — 从 CommentSentimentAnalyzer 提取.

被以下模块使用:
  - apps.api.services.analysis.sentiment  (CommentSentimentAnalyzer)

设计决策:
  - 将分词、词典匹配、否定词/强度修饰符处理独立出来，便于单元测试和词典迭代.
  - 保持零 NLP 依赖，纯 Python 实现.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class TokenScore:
    """单个 token 的评分结果."""
    final: float
    negated: bool


class SentimentTokenizer:
    """情感分词器 — 负责文本切分和 token 级情感评分."""

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

    def tokenize(self, text: str) -> list[str]:
        """分词：提取单词 + 表情符号.

        注意: 正则 \b 对中文字符的边界行为与 ASCII 不同，
        连续中文字符会被整体匹配为一个 token.
        这是原始 CommentSentimentAnalyzer 的行为，保持兼容.
        """
        words = re.findall(r"\b[a-zA-Z\u4e00-\u9fff]+\b", text.lower())
        emojis = re.findall(
            r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
            r"\U0001F680-\U0001F6FF\U00002702-\U000027B0"
            r"\U000024C2-\U0001F251\u2764\u2b50\u2728]", text
        )
        return words + emojis

    def score_token(self, tokens: list[str], index: int) -> TokenScore | None:
        """对单个 token 进行情感评分，考虑否定词和强度修饰符.

        Returns:
            TokenScore 或 None 当 token 不在词典中时.
        """
        token = tokens[index]
        if len(token) == 1 and ord(token) > 127:
            return TokenScore(self.EMOJI[token], False) if token in self.EMOJI else None

        is_pos = token in self._pos
        is_neg = token in self._neg
        if not is_pos and not is_neg:
            return None

        base = 1.0 if is_pos else -1.0
        modifier, negated = self._previous_token_modifier(tokens, index)
        final = base * modifier * (1.3 if token.isupper() and len(token) > 1 else 1.0)
        return TokenScore(final, negated)

    def score_tokens(self, tokens: list[str]) -> tuple[list[float], list[str], list[str]]:
        """对 token 列表批量评分.

        Returns:
            (scores, pos_words, neg_words)
        """
        scores: list[float] = []
        pos_words, neg_words = [], []
        for i, token in enumerate(tokens):
            scored = self.score_token(tokens, i)
            if scored is None:
                continue
            scores.append(scored.final)
            if scored.final > 0:
                pos_words.append(f"{token}(negated)" if scored.negated else token)
            elif scored.final < 0:
                neg_words.append(f"{token}(negated)" if scored.negated else token)
        return scores, pos_words, neg_words

    def _previous_token_modifier(self, tokens: list[str], index: int) -> tuple[float, bool]:
        """检查前一个 token 是否是否定词或强度修饰符."""
        if index <= 0:
            return 1.0, False
        prev = tokens[index - 1]
        if prev in self._negation:
            return -1.0, True
        if prev in self._intens:
            return 1.5, False
        return 1.0, False


# ── 评分聚合工具 ──

def compound_score(scores: list[float]) -> float:
    """将 token 分数列表合成为 [-1, 1] 的 compound score."""
    if not scores:
        return 0.0
    compound = sum(scores) / math.sqrt(sum(abs(s) for s in scores) ** 2 + 15)
    return max(-1.0, min(1.0, compound))


def score_percentages(scores: list[float], compound: float) -> tuple[float, float, float]:
    """计算 positive / negative / neutral 百分比."""
    pos_sum = sum(max(0, s) for s in scores)
    neg_sum = sum(max(0, -s) for s in scores)
    total = pos_sum + neg_sum
    if total <= 0:
        return 0.0, 0.0, 1.0
    pos_pct = pos_sum / total * abs(compound) if compound > 0 else 0
    neg_pct = neg_sum / total * abs(compound) if compound < 0 else 0
    return pos_pct, neg_pct, 1.0 - abs(compound)
