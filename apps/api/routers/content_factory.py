"""
内容工厂 Router — 选题发现 / 脚本辅助 / 分镜规划
路由前缀: /api/v1/content-factory

功能:
  - 热门话题发现 (基于频道历史数据推荐选题方向)
  - 视频结构模板库 (开场-主体-CTA 三段式等)
  - 分镜规划助手 (自动生成拍摄清单)
  - 标题/缩略图优化建议
  - SEO 关键词建议

设计决策:
  - 纯规则引擎, 无需 AI API 调用
  - 基于数据分析的选题推荐
  - 模板化脚本结构提供创作框架
"""
from __future__ import annotations

from collections import Counter
import logging
import json
import random
import re
from datetime import datetime
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import settings
from apps.api.services.analyzer import ThumbnailCTREstimator
from packages.db.schema import Video, get_db_session

router = APIRouter(prefix="/content-factory", tags=["Content Factory"])


# ── 视频结构模板库 ──

SCRIPT_TEMPLATES: dict[str, dict[str, Any]] = {
    "tutorial": {
        "name": "教程/教学模板",
        "name_en": "Tutorial Template",
        "structure": [
            {"section": "hook", "duration": "0:00-0:15", "purpose": "痛点提问或成果展示", "tips": "用具体数字或惊人结果开头"},
            {"section": "intro", "duration": "0:15-0:45", "purpose": "自我介绍+价值承诺", "tips": "说明你将要教什么, 观众能学到什么"},
            {"section": "prerequisites", "duration": "0:45-1:00", "purpose": "前置条件说明", "tips": "让观众确认自己是否适合继续看"},
            {"section": "main_content", "duration": "1:00-80%", "purpose": "核心教学内容 (分步骤)", "tips": "每3-5分钟一个小节, 用章节标记"},
            {"section": "summary", "duration": "80%-90%", "purpose": "要点回顾", "tips": "列出3-5个关键 takeaway"},
            {"section": "cta", "duration": "90%-100%", "purpose": "行动号召", "tips": "引导订阅/评论/查看相关视频"},
        ],
        "best_for": ["教程", "教学", "How-to", "技能分享"],
    },
    "review": {
        "name": "评测/开箱模板",
        "name_en": "Review Template",
        "structure": [
            {"section": "hook", "duration": "0:00-0:20", "purpose": "产品亮点速览", "tips": "先说结论: 值得买还是不值得"},
            {"section": "intro", "duration": "0:20-0:50", "purpose": "产品背景+评测标准", "tips": "说明你会从哪些维度评测"},
            {"section": "unboxing", "duration": "0:50-2:00", "purpose": "开箱/外观展示", "tips": "多角度展示, 注重细节特写"},
            {"section": "testing", "duration": "2:00-70%", "purpose": "实际测试/使用体验", "tips": "真实使用场景, 不是摆拍"},
            {"section": "pros_cons", "duration": "70%-85%", "purpose": "优缺点总结", "tips": "诚实说出缺点, 增加可信度"},
            {"section": "verdict", "duration": "85%-95%", "purpose": "最终结论+性价比分析", "tips": "明确推荐人群和不推荐人群"},
            {"section": "cta", "duration": "95%-100%", "purpose": "购买链接+互动", "tips": "联盟链接+询问观众问题"},
        ],
        "best_for": ["产品评测", "开箱", "App评测", "工具推荐"],
    },
    "storytelling": {
        "name": "故事叙述模板",
        "name_en": "Storytelling Template",
        "structure": [
            {"section": "hook", "duration": "0:00-0:20", "purpose": "悬念/冲突开场", "tips": "用一个惊人的事实或问题抓住注意力"},
            {"section": "context", "duration": "0:20-1:30", "purpose": "背景铺垫", "tips": "让观众理解故事的来龙去脉"},
            {"section": "rising_action", "duration": "1:30-60%", "purpose": "情节展开", "tips": "制造紧张感, 添加转折"},
            {"section": "climax", "duration": "60%-75%", "purpose": "高潮/关键转折点", "tips": "故事最精彩的部分, 充分展开"},
            {"section": "resolution", "duration": "75%-90%", "purpose": "结局/感悟", "tips": "总结经验和教训"},
            {"section": "cta", "duration": "90%-100%", "purpose": "互动号召", "tips": "让观众分享自己的类似经历"},
        ],
        "best_for": ["Vlog", "经历分享", "案例分析", "成功/失败故事"],
    },
    "comparison": {
        "name": "对比/排行榜模板",
        "name_en": "Comparison Template",
        "structure": [
            {"section": "hook", "duration": "0:00-0:15", "purpose": "对比主题引入", "tips": "说明为什么要对比这几个选项"},
            {"section": "intro", "duration": "0:15-0:45", "purpose": "对比维度说明", "tips": "列出评判标准 (价格/性能/易用性等)"},
            {"section": "option_a", "duration": "0:45-35%", "purpose": "第一个选项详解", "tips": "按统一维度逐一分析"},
            {"section": "option_b", "duration": "35%-60%", "purpose": "第二个选项详解", "tips": "保持与选项A相同的结构, 方便对比"},
            {"section": "option_c", "duration": "60%-80%", "purpose": "第三个选项详解", "tips": "如果有更多选项继续同样格式"},
            {"section": "comparison_table", "duration": "80%-92%", "purpose": "综合对比表", "tips": "用表格/图表总结, 一目了然"},
            {"section": "recommendation", "duration": "92%-100%", "purpose": "最终推荐+CTA", "tips": "明确说不同场景下推荐哪个"},
        ],
        "best_for": ["对比评测", "排行榜", "选购指南", "工具对比"],
    },
}


# ── 标题模板库 ──

TITLE_TEMPLATES: list[dict[str, Any]] = [
    {"template": "[数字]个[形容词][主题]技巧, 第[数字]个太厉害了", "category": "listicle", "ctr_boost": "high"},
    {"template": "为什么你的[主题]总是[问题]? 原因竟然是...", "category": "curiosity", "ctr_boost": "high"},
    {"template": "[主题]完整教程: 从[基础]到[高级] (新手必看)", "category": "tutorial", "ctr_boost": "medium"},
    {"template": "我用[方法]在[时间段][成果], 你也可以!", "category": "result", "ctr_boost": "high"},
    {"template": "[主题]的真相: 专家不会告诉你的[数字]个秘密", "category": "curiosity", "ctr_boost": "high"},
    {"template": "不要再[错误做法]了! [正确做法]才是答案", "category": "controversy", "ctr_boost": "high"},
    {"template": "[年份]年最新[主题]指南 (已更新)", "category": "freshness", "ctr_boost": "medium"},
    {"template": "[金额]元的[产品] vs [金额]元的[产品]: 差在哪?", "category": "comparison", "ctr_boost": "high"},
    {"template": "如何[目标] (即使[困难条件])", "category": "how_to", "ctr_boost": "medium"},
    {"template": "[名人/专家]的[主题]方法: 我试了[数字]天, 结果...", "category": "authority", "ctr_boost": "high"},
]


def _render_title_template(template: str, topic: str) -> str:
    replacements = {
        "[主题]": topic,
        "[数字]": str(random.randint(3, 10)),
        "[年份]": str(datetime.now().year),
        "[形容词]": random.choice(["超实用", "必看", "高效", "新手友好"]),
        "[问题]": random.choice(["没效果", "卡住", "浪费时间"]),
        "[基础]": "入门",
        "[高级]": "精通",
        "[方法]": random.choice(["系统方法", "实测流程", "自动化工具"]),
        "[时间段]": random.choice(["7天内", "一个月内", "一周内"]),
        "[成果]": random.choice(["提升效率", "做出结果", "完成变现验证"]),
        "[错误做法]": random.choice(["低效方法", "盲目跟风", "重复搬运"]),
        "[正确做法]": random.choice(["数据驱动", "先验证需求", "做差异化内容"]),
        "[金额]": random.choice(["99", "299", "999"]),
        "[产品]": topic,
        "[目标]": f"做好{topic}",
        "[困难条件]": "没有经验",
        "[名人/专家]": random.choice(["头部创作者", "增长专家", "资深从业者"]),
    }
    rendered = template
    for token, value in replacements.items():
        rendered = rendered.replace(token, value)
    # CRG: Prevent raw template tokens from leaking into user-facing factory suggestions.
    return re.sub(r"\[[^\]]+\]", topic, rendered)


@router.get("/topic-discovery")
async def topic_discovery(
    channel_id: Annotated[int | None, Query()] = None,
    niche: Annotated[str | None, Query()] = None,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
) -> dict[str, Any]:
    """选题发现 — 基于频道数据分析推荐选题方向.

    算法逻辑:
      1. 分析频道历史视频标题关键词频率
      2. 识别高表现视频的共同特征
      3. 结合热门标题模板生成选题建议
    """
    if channel_id and session:
        # CRG: Keep route orchestration separate from channel-video keyword analysis.
        return await _discover_channel_topics(channel_id, session, limit)
    return _discover_niche_topics(niche, limit)


async def _discover_channel_topics(channel_id: int, session: AsyncSession, limit: int) -> dict[str, Any]:
    result = await session.execute(
        select(Video)
        .where(Video.channel_id == channel_id)
        .order_by(desc(Video.view_count))
        .limit(20)
    )
    videos = result.scalars().all()
    if not videos:
        raise HTTPException(status_code=404, detail="No videos found for this channel")

    all_words = []
    for video in videos:
        all_words.extend(word for word in video.title.lower().split() if len(word) > 2)
    word_freq = Counter(all_words).most_common(10)

    avg_views = sum(video.view_count or 0 for video in videos) / max(len(videos), 1)
    top_videos = [video for video in videos if (video.view_count or 0) > avg_views * 1.5]

    topic_suggestions = []
    for i, (word, count) in enumerate(word_freq[:limit]):
        template = random.choice(TITLE_TEMPLATES)
        topic_suggestions.append({
            "topic_id": i + 1,
            "keyword": word,
            "frequency": count,
            "suggested_title": _render_title_template(template["template"], word),
            "title_template": template["template"],
            "template_category": template["category"],
            "estimated_ctr_boost": template["ctr_boost"],
            "inspiration_from": [video.title[:50] for video in top_videos[:2]],
        })

    return {
        "channel_id": channel_id,
        "analysis_basis": f"基于最近 {len(videos)} 个视频的分析",
        "top_keywords": [{"word": word, "count": count} for word, count in word_freq],
        "avg_views": round(avg_views, 2),
        "topic_suggestions": topic_suggestions,
    }


def _discover_niche_topics(niche: str | None, limit: int) -> dict[str, Any]:
    niches = {
        "tech": ["AI工具评测", "编程效率提升", "最新硬件开箱", "软件对比"],
        "education": ["学习方法", "考试技巧", "知识梳理", "错题分析"],
        "lifestyle": ["时间管理", "习惯养成", "极简生活", "晨间流程"],
        "finance": ["理财入门", "被动收入", "省钱技巧", "投资复盘"],
        "entertainment": ["热门反应", "挑战视频", "合作视频", "QA互动"],
    }
    suggestions = niches.get(niche or "general", ["选题建议"])
    return {
        "niche": niche or "general",
        "topic_suggestions": [
            {
                "topic_id": i + 1,
                "keyword": topic,
                "suggested_title": f"关于{topic}你需要知道的一切",
                "template_category": "general",
                "estimated_ctr_boost": "medium",
            }
            for i, topic in enumerate(suggestions[:limit])
        ],
    }


@router.get("/script-templates")
async def list_script_templates(
    category: Annotated[str | None, Query()] = None,
) -> list[dict[str, Any]]:
    """获取脚本结构模板列表."""
    templates = []
    for key, template in SCRIPT_TEMPLATES.items():
        if category and category not in template["best_for"]:
            continue
        templates.append({
            "template_id": key,
            "name": template["name"],
            "name_en": template["name_en"],
            "sections": len(template["structure"]),
            "best_for": template["best_for"],
            "structure_preview": [s["section"] for s in template["structure"]],
        })
    return templates


@router.get("/script-templates/{template_id}")
async def get_script_template(template_id: str) -> dict[str, Any]:
    """获取脚本模板详情."""
    if template_id not in SCRIPT_TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    return SCRIPT_TEMPLATES[template_id]


@router.post("/shot-list")
async def generate_shot_list(
    template_id: Annotated[str, Query()] = "tutorial",
    video_duration_minutes: Annotated[int, Query(ge=1, le=120)] = 10,
    camera_count: Annotated[int, Query(ge=1, le=4)] = 1,
    has_b_roll: Annotated[bool, Query()] = True,
) -> dict[str, Any]:
    """生成分镜拍摄清单.

    根据脚本模板和视频时长自动生成详细的拍摄计划.
    """
    if template_id not in SCRIPT_TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

    template = SCRIPT_TEMPLATES[template_id]
    total_duration_sec = video_duration_minutes * 60

    shot_list = [
        _build_section_shot_plan(section, total_duration_sec, camera_count, has_b_roll)
        for section in template["structure"]
    ]  # CRG: Move shot branching into helpers so the route only validates and assembles the response.

    total_shots = sum(len(s["shots"]) for s in shot_list)
    return {
        "template_id": template_id,
        "template_name": template["name"],
        "video_duration_minutes": video_duration_minutes,
        "total_shots": total_shots,
        "estimated_setup_time_minutes": max(5, total_shots * 2),
        "camera_count": camera_count,
        "has_b_roll": has_b_roll,
        "shot_list": shot_list,
        "equipment_checklist": _get_equipment_checklist(camera_count, has_b_roll),
    }


def _build_section_shot_plan(
    section: dict[str, Any],
    total_duration_sec: int,
    camera_count: int,
    has_b_roll: bool,
) -> dict[str, Any]:
    section_name = section["section"]
    duration_alloc = _calculate_section_duration(section_name, total_duration_sec)
    return {
        "section": section_name,
        "purpose": section["purpose"],
        "allocated_duration_sec": duration_alloc,
        "tips": section["tips"],
        "shots": _build_section_shots(section_name, duration_alloc, section["purpose"], has_b_roll),
        "camera_angles": ["主机位 (中景)"] + (["辅机位 (特写)"] if camera_count > 1 else []),
    }


def _build_section_shots(
    section_name: str,
    duration_alloc: int,
    purpose: str,
    has_b_roll: bool,
) -> list[dict[str, str]]:
    if section_name == "hook":
        return [
            {"shot": "特写 - 主讲人面部", "duration": f"0-{min(5, duration_alloc)}s", "note": "表情要有感染力"},
            {"shot": "文字叠加 - 核心数字/问题", "duration": f"0-{min(5, duration_alloc)}s", "note": "大字标题动画"},
        ]
    if section_name in ("main_content", "testing", "rising_action"):
        shots = [
            {"shot": f"中景 - 步骤 {i + 1} 演示", "duration": f"{i * 30}s-{(i + 1) * 30}s", "note": "清晰展示操作"}
            for i in range(min(max(2, duration_alloc // 30), 10))
        ]
        if has_b_roll:
            shots.append({"shot": "B-Roll - 相关画面/截图", "duration": "穿插", "note": "增加视觉丰富度"})
        return shots
    if section_name == "cta":
        return [
            {"shot": "中景 - 主讲人正面", "duration": f"0-{duration_alloc}s", "note": "真诚呼吁"},
            {"shot": "屏幕录制 - 订阅按钮动画", "duration": f"{max(0, duration_alloc - 3)}s-{duration_alloc}s", "note": "视觉引导"},
        ]
    return [{"shot": "中景/特写 - 主讲人", "duration": f"0-{duration_alloc}s", "note": purpose}]


def _calculate_section_duration(section_name: str, total_sec: int) -> int:
    """根据章节类型计算时长分配."""
    ratios = {
        "hook": 0.05, "intro": 0.07, "prerequisites": 0.03,
        "main_content": 0.50, "testing": 0.45, "rising_action": 0.35,
        "climax": 0.15, "pros_cons": 0.10, "comparison_table": 0.08,
        "summary": 0.07, "resolution": 0.10, "verdict": 0.08,
        "recommendation": 0.05, "cta": 0.05,
        "context": 0.12, "unboxing": 0.15, "option_a": 0.20,
        "option_b": 0.20, "option_c": 0.15,
    }
    ratio = ratios.get(section_name, 0.05)
    return max(5, int(total_sec * ratio))


def _get_equipment_checklist(camera_count: int, has_b_roll: bool) -> list[str]:
    """获取设备清单."""
    checklist = ["主机位相机/手机", "三脚架", "麦克风 (领夹麦/指向麦)", "补光灯"]
    if camera_count > 1:
        checklist.append("辅机位相机/手机")
        checklist.append("第二个三脚架")
    if has_b_roll:
        checklist.append("稳定器/云台 (B-Roll用)")
    checklist.extend(["充足存储空间", "备用电池/充电宝", "提词器 (可选)"])
    return checklist


@router.post("/title-optimization")
async def optimize_title(
    title: Annotated[str, Query(min_length=1)],
    target_audience: Annotated[str, Query()] = "general",
    has_face_in_thumbnail: Annotated[bool, Query()] = True,
    has_text_overlay: Annotated[bool, Query()] = True,
) -> dict[str, Any]:
    """标题优化建议 + 缩略图 CTR 估算.

    结合 Algorithm 8 (ThumbnailCTREstimator) 和标题模板匹配.
    """
    # CTR 估算
    ctr_result = ThumbnailCTREstimator.estimate(title, has_face_in_thumbnail, has_text_overlay)

    # 标题优化建议
    suggestions = []
    if len(title) < 30:
        suggestions.append("标题过短, 建议 40-60 字符以包含更多关键词")
    if len(title) > 80:
        suggestions.append("标题过长, 建议精简到 60 字符以内")
    if not any(c.isdigit() for c in title):
        suggestions.append("加入具体数字可提高 CTR (如 '5个技巧')")
    if "?" not in title and "?" not in title:
        suggestions.append("考虑使用疑问句式增加好奇心点击")
    if title.lower() == title or title.upper() == title:
        suggestions.append("适当使用首字母大写提高可读性")

    # 匹配最佳模板
    matched_templates = []
    for t in TITLE_TEMPLATES:
        score = _match_title_template(title, t["template"])
        if score > 0.3:
            matched_templates.append({
                "template": t["template"],
                "match_score": round(score, 2),
                "category": t["category"],
            })

    matched_templates.sort(key=lambda x: x["match_score"], reverse=True)

    return {
        "original_title": title,
        "title_length": len(title),
        "ctr_analysis": ctr_result,
        "optimization_suggestions": suggestions,
        "recommended_templates": matched_templates[:3],
        "improved_title_suggestions": _generate_improved_titles(title, matched_templates[:2]),
    }


def _match_title_template(actual: str, template: str) -> float:
    """简单模板匹配分数 (0-1)."""
    # 检查是否包含数字
    has_num = bool(any(c.isdigit() for c in actual))
    template_has_num = "[数字]" in template or "[年份]" in template or "[金额]" in template
    num_score = 0.3 if (has_num and template_has_num) or (not has_num and not template_has_num) else 0.0

    # 长度匹配
    len_score = 0.3 if 30 <= len(actual) <= 70 else 0.1

    # 关键词类别匹配
    category_score = 0.4  # 基础分
    template_lower = template.lower()
    actual_lower = actual.lower()
    if any(w in template_lower for w in ["教程", "指南", "tutorial"]):
        if any(w in actual_lower for w in ["教程", "指南", "教", "学", "how"]):
            category_score = 0.4

    return min(1.0, num_score + len_score + category_score)


def _generate_improved_titles(original: str, templates: list[dict]) -> list[str]:
    """基于模板生成改进的标题建议."""
    suggestions = []
    words = [word for word in original.strip().split() if word]
    keyword_str = " ".join(words[:4]) if words else "主题"
    # CRG: Preserve short but meaningful phrases like "AI tools" instead of dropping them by word length.

    for t in templates:
        template_str = t["template"]
        suggestions.append(_render_title_template(template_str, keyword_str))

    return suggestions


@router.get("/seo-keywords")
async def get_seo_keywords(
    topic: str,
    limit: Annotated[int, Query(ge=1, le=30)] = 10,
) -> dict[str, Any]:
    """获取 SEO 关键词建议 — 接入 YouTube Search Suggest API.

    数据来源:
      1. YouTube Search Suggest (真实搜索建议, 无需 API Key)
      2. 标题模板库匹配
      3. 长尾词扩展
    """
    suggestions, seen = await _fetch_youtube_suggest_keywords(topic)
    template_keywords = _build_template_keywords(topic, seen)
    base_keywords = _build_pattern_keywords(topic, seen)
    # CRG: Keep the route thin; keyword generation branches now live in testable helpers.
    all_keywords = suggestions + template_keywords + base_keywords

    _decorate_keyword_estimates(all_keywords[:limit])

    return {
        "topic": topic,
        "total_suggestions": len(all_keywords),
        "keywords": all_keywords[:limit],
        "recommendation": "优先选择标注为 'youtube_suggest' 的关键词（来自真实搜索建议）",
    }


def _parse_youtube_suggest_payload(text: str) -> list[str]:
    start = text.find("[[[")
    if start == -1:
        return []
    depth = 0
    end = start
    for pos, char in enumerate(text[start:], start):
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                end = pos + 1
                break
    data = json.loads(text[start:end])
    # CRG: Use bracket-depth parsing so JSONP wrappers with extra brackets do not corrupt keywords.
    return [item[0] for item in data[0] if item and item[0]]


async def _fetch_youtube_suggest_keywords(topic: str) -> tuple[list[dict[str, Any]], set[str]]:
    suggestions: list[dict[str, Any]] = []
    seen: set[str] = set()
    suffixes = ["", "how to", "tutorial", "review", "vs", "best", "beginner"]
    from apps.api.config import settings
    proxy = settings.PROXY_URL or None
    client_kwargs: dict[str, Any] = {"timeout": 10}
    if proxy:
        client_kwargs["proxy"] = proxy
    try:
        async with httpx.AsyncClient(**client_kwargs) as client:
            for suffix in suffixes:
                query = topic if not suffix else f"{topic} {suffix}"
                resp = await client.get(
                    "https://suggestqueries.google.com/complete/search",
                    params={"client": "youtube", "ds": "yt", "q": query},
                )
                category = "suggest" if not suffix else "long_tail"
                for kw in _parse_youtube_suggest_payload(resp.text):
                    if kw in seen:
                        continue
                    seen.add(kw)
                    suggestions.append({
                        "keyword": kw,
                        "category": category,
                        "search_intent": _get_intent("tutorial" if "how" in kw.lower() else "commercial"),
                        "source": "youtube_suggest",
                    })
    except Exception as e:
        logging.getLogger("seo").warning(f"YouTube Suggest API failed: {e}")
    return suggestions, seen


def _build_template_keywords(topic: str, seen: set[str]) -> list[dict[str, Any]]:
    keywords: list[dict[str, Any]] = []
    for template in TITLE_TEMPLATES:
        kw = _render_title_template(template["template"], topic)
        if kw in seen:
            continue
        seen.add(kw)
        keywords.append({
            "keyword": kw,
            "category": template["category"],
            "search_intent": _get_intent(template["category"]),
            "source": "template",
        })
    return keywords


def _build_pattern_keywords(topic: str, seen: set[str]) -> list[dict[str, Any]]:
    keywords: list[dict[str, Any]] = []
    keyword_patterns = {
        "tutorial": ["教程", "入门", "新手", "步骤", "怎么做", "完整版", "详细", "零基础"],
        "review": ["评测", "开箱", "体验", "值得买吗", "对比", "优缺点", "真实使用"],
        "comparison": ["vs", "对比", "哪个好", "区别", "选购指南", "推荐", "排行榜"],
        "tips": ["技巧", "秘诀", "效率", "方法", "小窍门", "最佳实践", "经验"],
    }
    for category, words in keyword_patterns.items():
        for word in words:
            for kw in (f"{topic} {word}", f"{word} {topic}"):
                if kw in seen:
                    continue
                seen.add(kw)
                keywords.append({
                    "keyword": kw,
                    "category": category,
                    "search_intent": _get_intent(category),
                    "source": "pattern",
                })
    return keywords


def _decorate_keyword_estimates(keywords: list[dict[str, Any]]) -> None:
    for i, keyword in enumerate(keywords):
        if keyword["source"] == "youtube_suggest":
            keyword["estimated_monthly_searches"] = random.randint(5000, 50000)
            keyword["competition"] = random.choice(["medium", "high"])
        elif keyword["source"] == "template":
            keyword["estimated_monthly_searches"] = random.randint(1000, 20000)
            keyword["competition"] = random.choice(["low", "medium"])
        else:
            keyword["estimated_monthly_searches"] = random.randint(100, 5000)
            keyword["competition"] = random.choice(["low", "medium", "high"])
        keyword["priority"] = i + 1


def _get_intent(category: str) -> str:
    intents = {
        "tutorial": "informational",
        "review": "commercial",
        "comparison": "commercial",
        "tips": "informational",
    }
    return intents.get(category, "informational")


# ── AI 脚本生成 ──

_SCRIPT_CONTENT_TEMPLATES: dict[str, dict[str, Any]] = {
    "tutorial": {
        "hook": [
            "你是不是也在为{topic}头疼？今天这期视频，我给你一个{adj}的解决方案。",
            "{topic}真的太让人崩溃了！但你知道吗？其实只要掌握这一个技巧，效率就能提升{num}倍。",
            "关于{topic}，我踩了无数的坑。今天把所有经验一次性分享给你。",
        ],
        "intro": [
            "大家好，欢迎来到频道。今天我们要聊的是{topic}。无论你是什么水平，这期视频都能让你有所收获。",
            "我是{host}，专注{topic}领域的内容创作。今天这期视频是我花了{time}整理出来的干货。",
        ],
        "prerequisites": [
            "在开始之前，你需要准备以下内容：{items}。",
            "这个教程适合{audience}。如果你符合这些条件，就可以跟着一起操作了。",
        ],
        "main_content": [
            "第一步：{step1}。这一步非常关键，决定了后续所有操作的成功与否。",
            "第二步：{step2}。注意这里的细节，很多人会在这个环节出错。",
            "第三步：{step3}。完成之后，你会发现效果立竿见影。",
        ],
        "summary": [
            "总结一下今天的内容：第一，{point1}；第二，{point2}；第三，{point3}。",
            "别忘了收藏这期视频，下次遇到{topic}相关问题时，直接回来看。",
        ],
        "cta": [
            "如果你觉得这期视频有帮助，记得点赞、订阅、开启小铃铛。有什么问题，欢迎在评论区交流。",
            "下期我会讲{next_topic}，不想错过的话，赶紧订阅吧！",
        ],
    },
    "review": {
        "hook": [
            "{product}到底值不值得买？我用了{time}，给你一个真实的答案。",
            "今天评测的是最近非常火的{product}。先说结论：{verdict}。",
        ],
        "intro": [
            "这期视频我会从{dimensions}几个维度，对{product}做一个全面的评测。",
        ],
        "unboxing": [
            "先来看一下包装。整体{packaging}，配件包括{accessories}。",
            "外观设计{design}，做工{craftsmanship}，这个价位来说{value}。",
        ],
        "testing": [
            "实际使用中，{feature1}的表现{performance1}。",
            "{feature2}是我比较关注的功能，测试结果{performance2}。",
        ],
        "pros_cons": [
            "优点方面：第一{pro1}；第二{pro2}。\n缺点方面：第一{con1}；第二{con2}。",
        ],
        "verdict": [
            "综合来看，{product}适合{target_user}。如果你{condition}，那这款产品{recommendation}。",
        ],
        "cta": [
            "购买链接放在评论区置顶，需要的朋友可以自取。记得点赞订阅，我们下期见！",
        ],
    },
    "storytelling": {
        "hook": [
            "你知道吗？关于{topic}，我经历过一件{adj}的事。",
            "今天想和大家分享一个{topic}的真实故事，可能会改变你的看法。",
        ],
        "context": [
            "事情发生在{time}，当时的{situation}。",
        ],
        "rising_action": [
            "最开始{event1}。然后{event2}。事情开始变得{direction}。",
        ],
        "climax": [
            "最关键的时刻到了。{climax_event}。那一刻我真的{feeling}。",
        ],
        "resolution": [
            "最后{outcome}。这件事让我明白了一个道理：{lesson}。",
        ],
        "cta": [
            "你有类似的经历吗？欢迎在评论区分享你的故事。",
        ],
    },
    "comparison": {
        "hook": [
            "{option_a}和{option_b}到底怎么选？今天给你一个{adj}的对比。",
            "很多人在{topic}上纠结，到底该选哪个？这期视频给你答案。",
        ],
        "intro": [
            "我们会从{dimensions}这几个维度进行对比。",
        ],
        "option_a": [
            "先看{option_a}。{desc_a}",
        ],
        "option_b": [
            "再看{option_b}。{desc_b}",
        ],
        "option_c": [
            "第三个选项{option_c}。{desc_c}",
        ],
        "comparison_table": [
            "总结一下对比结果：在{aspect1}上，{winner1}更优；在{aspect2}上，{winner2}更优。",
        ],
        "recommendation": [
            "如果你{condition_a}，推荐选{rec_a}；如果你{condition_b}，推荐选{rec_b}。",
        ],
    },
}


_SCRIPT_SEGMENT_TYPE_MAP: dict[str, str] = {
    "hook": "hook", "intro": "pain", "prerequisites": "pain",
    "context": "pain", "main_content": "solution", "testing": "demo",
    "unboxing": "demo", "rising_action": "solution", "climax": "solution",
    "pros_cons": "solution", "verdict": "solution", "summary": "solution",
    "resolution": "solution", "comparison_table": "solution",
    "recommendation": "solution", "cta": "cta",
    "option_a": "solution", "option_b": "solution", "option_c": "solution",
}

_SCRIPT_SEGMENT_LABEL_MAP: dict[str, str] = {
    "hook": "Hook 开场", "intro": "引入/痛点", "prerequisites": "前置说明",
    "context": "背景铺垫", "main_content": "核心内容", "testing": "实测演示",
    "unboxing": "开箱展示", "rising_action": "情节展开", "climax": "高潮转折",
    "pros_cons": "优缺点", "verdict": "最终结论", "summary": "要点回顾",
    "resolution": "结局感悟", "comparison_table": "对比总结",
    "recommendation": "最终推荐", "cta": "CTA 行动",
    "option_a": "选项A详解", "option_b": "选项B详解", "option_c": "选项C详解",
}

_SCRIPT_TOPIC_REPLACEMENTS: dict[str, str] = {
    "{step1}": "理解{topic}的核心概念",
    "{step2}": "掌握{topic}的关键操作",
    "{step3}": "应用{topic}解决实际问题",
    "{point1}": "{topic}的基本原理",
    "{point2}": "{topic}的实操技巧",
    "{point3}": "{topic}的常见误区",
    "{next_topic}": "进阶{topic}技巧",
    "{target_user}": "对{topic}有需求的用户",
    "{condition}": "预算充足且注重{topic}体验",
    "{situation}": "{topic}正处于关键时期",
    "{lesson}": "面对{topic}，坚持和耐心是最重要的",
}

_SCRIPT_STATIC_REPLACEMENTS: dict[str, str] = {
    "{items}": "相关资料和工具",
    "{audience}": "对此话题感兴趣的观众",
    "{dimensions}": "外观、性能、价格",
    "{accessories}": "说明书、数据线等",
    "{feature1}": "核心功能",
    "{feature2}": "附加功能",
    "{pro1}": "功能全面",
    "{pro2}": "易于上手",
    "{con1}": "价格偏高",
    "{con2}": "续航一般",
    "{event1}": "遇到了第一个挑战",
    "{event2}": "情况发生了变化",
    "{direction}": "复杂起来",
    "{climax_event}": "做出了一个关键决定",
    "{outcome}": "事情得到了圆满解决",
    "{option_a}": "方案A",
    "{option_b}": "方案B",
    "{option_c}": "方案C",
    "{desc_a}": "这是一个经典的选择，稳定可靠。",
    "{desc_b}": "这个方案更具创新性，适合追求新鲜感的用户。",
    "{desc_c}": "这是一个折中方案，兼顾了稳定性和创新性。",
    "{aspect1}": "核心功能",
    "{aspect2}": "性价比",
    "{winner1}": "方案A",
    "{winner2}": "方案B",
    "{condition_a}": "注重稳定性",
    "{condition_b}": "喜欢尝鲜",
    "{rec_a}": "方案A",
    "{rec_b}": "方案B",
}

_SCRIPT_RANDOM_REPLACEMENTS: dict[str, list[str]] = {
    "{verdict}": ["值得入手", "谨慎考虑", "性价比不错"],
    "{packaging}": ["简洁", "精致", "中规中矩"],
    "{design}": ["很时尚", "比较保守", "有辨识度"],
    "{craftsmanship}": ["扎实", "一般", "精细"],
    "{value}": ["还算值", "性价比一般", "非常划算"],
    "{performance1}": ["超出预期", "符合预期", "略低于预期"],
    "{performance2}": ["表现不错", "中规中矩", "有待改进"],
    "{recommendation}": ["非常推荐", "可以考虑", "按需购买"],
    "{feeling}": ["非常激动", "五味杂陈", "豁然开朗"],
}


@router.post("/ai-script")
async def ai_script_generate(
    niche: Annotated[str, Query()] = "general",
    template_id: Annotated[str, Query()] = "tutorial",
    topic: Annotated[str, Query()] = "",
) -> dict[str, Any]:
    """AI 生成脚本 — 基于模板 + 规则引擎填充内容.

    无需 LLM API，根据 niche/topic 自动填充各段落脚本内容.
    """
    if template_id not in SCRIPT_TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

    template = SCRIPT_TEMPLATES[template_id]
    structure = template["structure"]
    content_templates = _SCRIPT_CONTENT_TEMPLATES.get(template_id, {})

    topic_kw = topic or niche or "这个话题"
    adj = random.choice(["超实用", "必看", "终极", "高效", "简单"])
    num = random.randint(3, 10)
    host = random.choice(["主播", "UP主", "创作者"])
    time_span = random.choice(["一周", "一个月", "三个月"])
    replacements = _build_script_replacements(topic_kw, adj, num, host, time_span)
    segments = [
        _build_script_segment(template_id, index, section, content_templates, replacements)
        for index, section in enumerate(structure)
    ]  # CRG: Template rendering is data-driven instead of embedding every replacement inside the route.

    return {
        "template_id": template_id,
        "template_name": template["name"],
        "niche": niche,
        "topic": topic_kw,
        "segments": segments,
    }


def _build_script_replacements(
    topic_kw: str,
    adj: str,
    num: int,
    host: str,
    time_span: str,
) -> dict[str, str]:
    replacements = {
        "{topic}": topic_kw,
        "{product}": topic_kw,
        "{adj}": adj,
        "{num}": str(num),
        "{host}": host,
        "{time}": time_span,
    }
    replacements.update({
        token: template.format(topic=topic_kw)
        for token, template in _SCRIPT_TOPIC_REPLACEMENTS.items()
    })
    replacements.update(_SCRIPT_STATIC_REPLACEMENTS)
    replacements.update({
        token: random.choice(options)
        for token, options in _SCRIPT_RANDOM_REPLACEMENTS.items()
    })
    return replacements


def _build_script_segment(
    template_id: str,
    index: int,
    section: dict[str, Any],
    content_templates: dict[str, list[str]],
    replacements: dict[str, str],
) -> dict[str, Any]:
    section_name = section["section"]
    templates = content_templates.get(section_name, [""])
    content = random.choice(templates) if templates else ""
    for token, value in replacements.items():
        content = content.replace(token, value)
    return {
        "id": f"seg-{template_id}-{index}",
        "type": _SCRIPT_SEGMENT_TYPE_MAP.get(section_name, "solution"),
        "title": _SCRIPT_SEGMENT_LABEL_MAP.get(section_name, section_name),
        "content": content,
        "duration": 30,
        "purpose": section.get("purpose", ""),
        "tips": section.get("tips", ""),
    }


@router.post("/thumbnail-suggestions")
async def thumbnail_suggestions(
    title: Annotated[str, Query(min_length=1)],
    niche: Annotated[str, Query()] = "general",
    has_face: Annotated[bool, Query()] = True,
    has_text: Annotated[bool, Query()] = True,
) -> dict[str, Any]:
    """Generate practical thumbnail directions and CTR diagnostics."""
    ctr = ThumbnailCTREstimator.estimate(title, has_face, has_text)
    title_words = [w for w in title.replace("：", " ").replace(":", " ").split() if w]
    focus = title_words[0] if title_words else niche

    concepts = [
        {
            "name": "结果对比型",
            "layout": "左侧展示问题状态，右侧展示结果状态，中间用高对比箭头连接",
            "text_overlay": f"{focus}前后对比",
            "visual_hook": "强反差、数字结果、清晰主体",
            "best_for": ["tutorial", "case_study", "growth"],
        },
        {
            "name": "冲突悬念型",
            "layout": "主体人物/产品占 60%，右上角放一个醒目的疑问短句",
            "text_overlay": "真的有效吗?",
            "visual_hook": "表情、疑问、未揭晓结果",
            "best_for": ["review", "commentary", "analysis"],
        },
        {
            "name": "清单工具型",
            "layout": "三列图标或步骤卡片，标题保留 3 到 5 个字",
            "text_overlay": "3步搞定",
            "visual_hook": "步骤感、低认知负担、可收藏",
            "best_for": ["how_to", "education", "tooling"],
        },
    ]

    mistakes = []
    if len(title) > 70:
        mistakes.append("标题偏长，缩略图文字应压缩到 6 个汉字或 3 个英文词以内")
    if not has_face:
        mistakes.append("如果内容适合真人出镜，加入脸部或手部动作通常能提高停留注意力")
    if not has_text:
        mistakes.append("建议增加极短文字锚点，避免缩略图只靠画面表达")
    if not mistakes:
        mistakes.append("当前基础元素完整，优先做 A/B 版本测试颜色和文字长度")

    return {
        "title": title,
        "niche": niche,
        "ctr_analysis": ctr,
        "concepts": concepts,
        "checklist": [
            "文字不超过 6 个汉字或 3 个英文词",
            "主体面积至少占画面 45%",
            "背景保持干净，不要和标题争抢注意力",
            "移动端 20% 缩放后仍能看清核心信息",
            "至少导出 2 个版本做 A/B 测试",
        ],
        "common_mistakes": mistakes,
    }


@router.post("/publish-time-optimization")
async def publish_time_optimization(
    niche: Annotated[str, Query()] = "general",
    target_region: Annotated[str, Query()] = settings.DEFAULT_TARGET_REGION,
    video_length_minutes: Annotated[int, Query(ge=1, le=240)] = 10,
) -> dict[str, Any]:
    """Recommend publishing windows using niche and audience-region heuristics."""
    region_windows = {
        "china": ["12:00-13:30", "19:30-22:30"],
        "us": ["07:00-09:00", "17:00-21:00"],
        "europe": ["08:00-10:00", "18:00-21:00"],
        "global": ["12:00-14:00", "18:00-22:00"],
    }
    niche_days = {
        "finance": ["Tuesday", "Wednesday", "Thursday"],
        "education": ["Sunday", "Monday", "Tuesday"],
        "tech": ["Tuesday", "Wednesday", "Friday"],
        "lifestyle": ["Friday", "Saturday", "Sunday"],
        "entertainment": ["Friday", "Saturday", "Sunday"],
    }

    windows = region_windows.get(target_region.lower(), region_windows["global"])
    days = niche_days.get(niche.lower(), ["Tuesday", "Thursday", "Saturday"])
    preheat_hours = 24 if video_length_minutes >= 12 else 6

    return {
        "niche": niche,
        "target_region": target_region,
        "recommended_days": days,
        "time_windows": [
            {
                "window": w,
                "reason": "覆盖通勤、午休或晚间高活跃时段",
                "priority": i + 1,
            }
            for i, w in enumerate(windows)
        ],
        "release_playbook": [
            f"发布前 {preheat_hours} 小时准备标题、缩略图和首条置顶评论",
            "发布后 30 分钟内回复早期评论，放大互动信号",
            "发布后 2 小时检查 CTR 和平均观看时长，必要时更换缩略图",
            "24 小时后复盘流量来源，把表现好的关键词沉淀到下一期选题",
        ],
        "experiment": {
            "test_period_days": 14,
            "variants": [
                {"name": "晚间黄金档", "time": windows[-1]},
                {"name": "午间轻决策档", "time": windows[0]},
            ],
            "success_metric": "前 24 小时 CTR、平均观看时长、每千曝光订阅转化",
        },
    }


_HUMAN_REVIEW_BASE_ITEMS: list[dict[str, str]] = [
    {
        "id": "topic-decision",
        "stage": "Topic",
        "title": "Topic decision log",
        "evidence": "Selected topic, rejected alternatives, target viewer, and reason for expected demand.",
        "why": "Shows human editorial input and avoids fully automated bulk publishing.",
    },
    {
        "id": "source-provenance",
        "stage": "Research",
        "title": "Source provenance",
        "evidence": "Original URLs, notes, screenshots, data timestamps, and any license constraints.",
        "why": "Reduces copyright risk and makes claims traceable.",
    },
    {
        "id": "script-revision",
        "stage": "Script",
        "title": "Human script revision",
        "evidence": "Before/after script notes, added opinions, corrections, examples, or demonstrations.",
        "why": "Documents substantial transformation instead of raw AI output.",
    },
    {
        "id": "asset-rights",
        "stage": "Assets",
        "title": "Asset rights check",
        "evidence": "Music, footage, screenshots, voice, image, and font usage notes.",
        "why": "Prevents reusable-content and copyright issues.",
    },
    {
        "id": "thumbnail-title-ab",
        "stage": "Packaging",
        "title": "Title and thumbnail A/B record",
        "evidence": "Two title variants, two thumbnail variants, expected CTR driver, final pick.",
        "why": "Connects packaging choices to measurable experiments.",
    },
    {
        "id": "final-review",
        "stage": "Publish",
        "title": "Final human review",
        "evidence": "Fact check, disclosure decision, monetization suitability, and publish-time notes.",
        "why": "Creates a release gate before uploading.",
    },
    {
        "id": "postmortem",
        "stage": "Post-publish",
        "title": "24h performance review",
        "evidence": "CTR, retention, comments, traffic source, next experiment.",
        "why": "Feeds the intelligence system back into the next video.",
    },
]

_HUMAN_REVIEW_AI_TOOL_ITEMS: list[dict[str, str]] = [
    {
        "id": "screen-demo-proof",
        "stage": "Production",
        "title": "Screen demo proof",
        "evidence": "Recorded operation steps, result screenshots, and limitations found during testing.",
        "why": "For AI tool tutorials, real use is the strongest differentiator.",
    },
    {
        "id": "affiliate-disclosure",
        "stage": "Monetization",
        "title": "Affiliate disclosure",
        "evidence": "Pinned comment, description disclosure, link target, and product-fit reason.",
        "why": "Keeps monetization transparent and aligned with the audience.",
    },
]


@router.get("/human-review-checklist")
async def human_review_checklist(
    niche: Annotated[str, Query()] = settings.DEFAULT_NICHE,
    video_type: Annotated[str, Query()] = settings.DEFAULT_VIDEO_TYPE,
) -> dict[str, Any]:
    """Return a human-in-the-loop review and evidence checklist."""
    items = list(_HUMAN_REVIEW_BASE_ITEMS)
    if niche in {"ai_tools", "tech", "saas"}:
        items.extend(_HUMAN_REVIEW_AI_TOOL_ITEMS)
    # CRG: Keep static checklist data outside the route so the endpoint remains a thin API adapter.

    return {
        "niche": niche,
        "video_type": video_type,
        "blueprint_source": "KimiAgent TubeFactory research synthesis: human decision + AI execution + evidence trail",
        "minimum_publish_gate": [
            "topic-decision",
            "source-provenance",
            "script-revision",
            "asset-rights",
            "final-review",
        ],
        "checklist": items,
        "recommended_folder": "data/evidence/{video_slug}/",
        "file_suggestions": [
            "topic_decision.md",
            "source_notes.md",
            "script_revision.md",
            "asset_rights.md",
            "publish_review.md",
            "24h_postmortem.md",
        ],
    }
