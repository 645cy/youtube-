"""Tests for content_factory helper branches that do not need network calls."""
from __future__ import annotations

from apps.api.routers import content_factory


def test_parse_youtube_suggest_payload_extracts_keywords() -> None:
    payload = 'window.google.ac.h([["ai"],[[["ai tools"],["ai tutorial"]]]])'
    assert content_factory._parse_youtube_suggest_payload(payload) == ["ai tools", "ai tutorial"]


def test_template_and_pattern_keywords_are_deduped() -> None:
    seen: set[str] = set()
    templates = content_factory._build_template_keywords("AI", seen)
    patterns = content_factory._build_pattern_keywords("AI", seen)
    keywords = [item["keyword"] for item in templates + patterns]
    assert len(keywords) == len(set(keywords))
    assert all("[" not in keyword and "]" not in keyword for keyword in keywords)
    assert any(item["source"] == "pattern" for item in patterns)  # CRG: Keyword fallback stays available offline.


def test_title_template_renderer_removes_user_visible_tokens() -> None:
    rendered = content_factory._render_title_template("[数字]个[形容词][主题]技巧: 解决[问题]", "AI")
    assert "AI" in rendered
    assert "[" not in rendered and "]" not in rendered  # CRG: Factory suggestions must not leak raw placeholders.


def test_improved_titles_preserve_short_topic_words() -> None:
    suggestions = content_factory._generate_improved_titles(
        "AI tools tutorial",
        [{"template": "为什么你的[主题]总是[问题]? 原因竟然是..."}],
    )
    assert "AI tools tutorial" in suggestions[0]
    assert "[" not in suggestions[0] and "]" not in suggestions[0]  # CRG: Title suggestions should read like output.


def test_keyword_estimates_add_priority_and_competition() -> None:
    keywords = [{"keyword": "AI tutorial", "source": "pattern"}]
    content_factory._decorate_keyword_estimates(keywords)
    assert keywords[0]["priority"] == 1
    assert "competition" in keywords[0]  # CRG: Factory UI depends on decorated keyword metadata.
