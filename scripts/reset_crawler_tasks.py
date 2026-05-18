"""删除所有旧爬虫任务，创建 AI 相关的高播放频道发现任务。"""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone

sys.path.insert(0, r"D:\Projects\YouTube\tubefactory-ocp")

from sqlalchemy import delete, select
from packages.db.schema import CrawlerTask, CrawlerTaskRun, get_sessionmaker

# ── AI 相关 / AI 能制作的内容（关键词混合带 AI 和不带 AI 的具体工具名/场景） ──
TASKS = [
    {
        "name": "发现-AI视频生成",
        "keywords": [
            "AI video generator", "Sora OpenAI", "Runway tutorial",
            "text to video", "Pika Labs", "Kling AI",
            "HeyGen tutorial", "Synthesia video", "D-ID avatar",
            "AI video editing", "CapCut AI features", "Descript video",
            "Opus Clip", "AI cinematic", "AI movie making",
            "AI lip sync", "AI video upscaling", "AI face swap video",
            "Runway Gen", "invideo AI", "Fliki tutorial",
        ],
    },
    {
        "name": "发现-AI绘画设计",
        "keywords": [
            "Midjourney tutorial", "Stable Diffusion guide", "DALL E 3",
            "AI art generator", "Leonardo AI", "Adobe Firefly",
            "ComfyUI workflow", "LoRA training", "ControlNet",
            "text to image", "AI character design", "AI concept art",
            "AI logo design", "AI illustration", "Canva AI",
            "AI fashion design", "AI interior design", "AI pixel art",
            "AI anime generator", "AI tattoo design", "Ideogram AI",
        ],
    },
    {
        "name": "发现-AI音乐音频",
        "keywords": [
            "AI music generator", "Suno music", "Udio AI",
            "text to music", "AI voice clone", "ElevenLabs",
            "AI singing voice", "AI sound design", "AI audio editing",
            "AI podcast voice", "AI royalty free music", "AI beat maker",
            "AI mastering", "Murf AI", "PlayHT",
            "AI speech synthesis", "AI ambient music", "AI remix",
            "Boomy AI", "AIVA music", "Voicify AI",
        ],
    },
    {
        "name": "发现-AI编程开发",
        "keywords": [
            "GitHub Copilot", "Cursor AI editor", "ChatGPT coding",
            "AI coding assistant", "Codeium", "Tabnine",
            "AI code review", "Replit Ghostwriter", "Claude coding",
            "AI app builder", "no code AI", "v0 dev",
            "AI software development", "AI bug fix", "AI API integration",
            "AI automation script", "Bolt new", "Lovable dev",
            "AI web scraping", "AI database", "AI dev tools",
        ],
    },
    {
        "name": "发现-AI写作内容",
        "keywords": [
            "AI writing assistant", "ChatGPT content", "Jasper AI",
            "AI copywriting", "Copy AI", "Writesonic",
            "AI blog writer", "AI script writing", "AI story generator",
            "AI SEO content", "AI email writer", "AI social media captions",
            "AI book writing", "AI academic writing", "Notion AI",
            "AI summarization", "AI paraphrasing", "Grammarly",
            "AI content strategy", "AI title generator", "AI hook writing",
        ],
    },
    {
        "name": "发现-AI电商营销",
        "keywords": [
            "AI marketing", "AI product photo", "AI ad creator",
            "AI ecommerce", "AI dropshipping", "AI customer service",
            "AI sales copy", "AI brand strategy", "AI influencer",
            "AI social media marketing", "AI email marketing", "AI funnel",
            "AI pricing strategy", "AI market research", "AI affiliate",
            "Shopify AI", "Amazon AI tools", "AI video ads",
            "AI landing page", "AI marketing automation", "AI CRM",
        ],
    },
    {
        "name": "发现-AI教育学习",
        "keywords": [
            "AI tutor", "AI course creator", "AI learning platform",
            "AI language learning", "AI math solver", "AI exam prep",
            "AI study assistant", "AI homework help", "AI flashcards",
            "AI quiz generator", "AI classroom", "AI personalized learning",
            "AI kids education", "AI science experiments", "AI skill assessment",
            "Khanmigo", "Duolingo Max", "Quizlet AI",
            "AI tutoring app", "AI learning path", "AI study planner",
        ],
    },
    {
        "name": "发现-AI3D动画",
        "keywords": [
            "AI 3D model", "Meshy AI", "Rodin AI",
            "text to 3D", "Tripo 3D", "Luma AI",
            "AI character animation", "AI motion capture", "AI rigging",
            "AI game assets", "AI voxel art", "AI architectural render",
            "AI visual effects", "AI CGI", "AI texture generation",
            "AI environment design", "AI product render", "AI avatar 3D",
            "Kaedim 3D", "Spline AI", "CSM 3D",
        ],
    },
    {
        "name": "发现-AI虚拟人直播",
        "keywords": [
            "AI virtual influencer", "AI VTuber", "AI digital human",
            "AI news anchor", "AI live stream", "AI presenter",
            "AI avatar creator", "AI talking head", "AI face swap",
            "character AI", "AI roleplay", "AI companion",
            "AI synthetic media", "AI persona", "AI interactive video",
            "Unreal Engine MetaHuman", "Replika AI", "Soulmate AI",
            "AI live streaming tools", "AI streamer", "AI broadcast",
        ],
    },
    {
        "name": "发现-AI工具测评",
        "keywords": [
            "AI tools comparison", "best AI tools", "AI software review",
            "AI productivity tools", "AI workflow", "AI platform review",
            "free AI tools", "AI chrome extensions", "AI plugin review",
            "AI SaaS review", "AI startup tools", "AI enterprise tools",
            "AI API comparison", "AI model benchmark", "AI tool stack",
            "Futurepedia", "TheresAnAIForThat", "AI news",
            "AI industry update", "AI tool directory", "AI roundup",
        ],
    },
    {
        "name": "发现-AI游戏互动",
        "keywords": [
            "AI game development", "AI NPC", "AI procedural generation",
            "AI game design", "AI Unity", "AI Unreal Engine",
            "AI game art", "AI game music", "AI game testing",
            "AI text adventure", "AI interactive story", "AI game bot",
            "AI VR game", "AI metaverse", "AI gamification",
            "Inworld AI", "Convai", "AI dungeon",
            "AI narrative design", "AI level design", "AI enemy AI",
        ],
    },
    {
        "name": "发现-AI摄影修图",
        "keywords": [
            "AI photo editor", "Luminar Neo", "Topaz Photo AI",
            "AI image enhancement", "AI photo restoration", "AI background removal",
            "AI portrait editing", "AI photo retouch", "AI color grading",
            "AI photo animation", "AI old photo repair", "AI style transfer",
            "AI face enhancement", "AI batch editing", "AI watermark removal",
            "AI photo compositing", "AI lens simulation", "AI photo generator",
            "Photoshop AI", "Lightroom AI", "AI photography tips",
        ],
    },
    {
        "name": "发现-AI短视频社媒",
        "keywords": [
            "AI TikTok", "AI YouTube Shorts", "AI Reels",
            "AI viral content", "AI trending", "AI hashtag",
            "AI thumbnail", "AI title", "AI video hook",
            "AI faceless channel", "AI automation YouTube", "AI content repurposing",
            "AI clip generator", "AI subtitle", "AI voiceover",
            "Submagic", "Klap", "Munch AI",
            "AI short form", "AI content creation", "AI social media manager",
        ],
    },
    {
        "name": "发现-AI自动化工作流",
        "keywords": [
            "AI workflow automation", "Make automation", "Zapier AI",
            "AI RPA", "n8n workflow", "Bardeen AI",
            "AI agent workflow", "AI task automation", "AI data pipeline",
            "AI business automation", "AI meeting notes", "AI calendar",
            "AI email automation", "AI CRM", "AI document processing",
            "Autogen", "Crew AI", "LangChain",
            "AI agent builder", "AI orchestration", "AI no code",
        ],
    },
    {
        "name": "发现-AI科研数据分析",
        "keywords": [
            "AI data analysis", "AI research tool", "AI paper summary",
            "AI literature review", "AI statistical analysis", "AI visualization",
            "AI chart generator", "AI Excel", "AI SQL",
            "AI predictive model", "AI trend analysis", "AI survey analysis",
            "Elicit AI", "Consensus AI", "SciSpace",
            "AI biotech", "AI drug discovery", "AI climate model",
            "AI financial analysis", "AI stock prediction", "AI research assistant",
        ],
    },
]

DEFAULT_CONFIG = {
    "max_results_per_keyword": 50,
    "max_channel_age_months": 240,
    "max_video_count": 9999,
}


async def main():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        old_run_count_result = await session.execute(select(CrawlerTaskRun))
        old_run_count = len(old_run_count_result.scalars().all())
        await session.execute(delete(CrawlerTaskRun))
        print(f"已删除 {old_run_count} 条 CrawlerTaskRun")

        old_task_count_result = await session.execute(select(CrawlerTask))
        old_task_count = len(old_task_count_result.scalars().all())
        await session.execute(delete(CrawlerTask))
        print(f"已删除 {old_task_count} 条 CrawlerTask")

        created = []
        for t in TASKS:
            config = {**DEFAULT_CONFIG, "keywords": t["keywords"]}
            task = CrawlerTask(
                name=t["name"],
                task_type="channel_discovery",
                target=", ".join(t["keywords"]),
                frequency="weekly",
                status="active",
                config_json=json.dumps(config, ensure_ascii=False),
                next_run_at=datetime.now(timezone.utc),
            )
            session.add(task)
            created.append(task)

        await session.commit()

        for task in created:
            await session.refresh(task)

        total_keywords = sum(len(t["keywords"]) for t in TASKS)
        print(f"\n创建了 {len(created)} 个新 CrawlerTask")
        print(f"   总共 {total_keywords} 个关键词")
        print(f"   每词 {DEFAULT_CONFIG['max_results_per_keyword']} 个结果")
        print(f"   筛选条件: max_age={DEFAULT_CONFIG['max_channel_age_months']}月, "
              f"max_video={DEFAULT_CONFIG['max_video_count']}")
        print(f"   评分逻辑: 总播放量 + 平均播放量 + 订阅数，高播放频道排前面")
        print(f"   调度频率: weekly")
        for task in created:
            cfg = json.loads(task.config_json)
            print(f"   - [{task.id}] {task.name} ({len(cfg['keywords'])} 关键词)")


if __name__ == "__main__":
    asyncio.run(main())
