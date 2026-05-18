"""追加更多 AI 相关领域的 channel_discovery 任务."""
import asyncio
import json
import sys
sys.path.insert(0, r"D:\Projects\YouTube\tubefactory-ocp")

from datetime import datetime, timezone
from packages.db.schema import CrawlerTask, get_sessionmaker

TASKS = [
    {
        "name": "发现-AI新闻",
        "keywords": [
            "AI news", "tech news AI", "artificial intelligence daily",
            "AI breakthrough", "machine learning news", "AI update",
            "future of AI", "AI trends", "OpenAI news", "Google AI",
            "Meta AI", "Microsoft AI", "AI industry", "AI technology",
            "robotics news", "AI ethics", "AI regulation", "AI policy",
            "deep learning news", "neural network news",
        ],
    },
    {
        "name": "发现-AI投资",
        "keywords": [
            "AI stocks", "AI investment", "artificial intelligence trading",
            "AI finance", "fintech AI", "algorithmic trading",
            "AI hedge fund", "quant trading", "AI market analysis",
            "AI portfolio", "crypto AI", "AI trading bot", "stock AI",
            "AI wealth management", "robo advisor", "AI prediction",
            "AI venture capital", "AI startup funding", "AI IPO",
            "AI economic",
        ],
    },
    {
        "name": "发现-AI医疗",
        "keywords": [
            "AI healthcare", "medical AI", "AI diagnosis",
            "AI drug discovery", "AI biology", "AI medicine",
            "health AI", "AI medical imaging", "AI clinical",
            "AI therapy", "AI mental health", "AI fitness",
            "AI nutrition", "AI biomedical", "AI pharma",
            "AI patient care", "AI surgery", "AI radiology",
            "AI pathology", "AI telemedicine",
        ],
    },
    {
        "name": "发现-AI法律",
        "keywords": [
            "AI law", "legal AI", "AI compliance", "AI regulation",
            "AI policy", "AI governance", "AI ethics",
            "AI lawyer", "AI contract", "AI copyright",
            "AI patent", "AI intellectual property", "AI privacy",
            "AI data protection", "AI risk", "AI audit",
            "AI standards", "AI framework", "AI legislation",
            "AI liability",
        ],
    },
    {
        "name": "发现-AI制造",
        "keywords": [
            "AI manufacturing", "industrial AI", "AI factory",
            "AI robotics", "AI automation", "AI quality control",
            "AI supply chain", "AI logistics", "AI warehouse",
            "AI Industry 4.0", "smart manufacturing", "AI production",
            "AI maintenance", "AI inspection", "AI CNC",
            "AI 3D print", "AI material", "AI design engineering",
            "AI simulation", "AI digital twin",
        ],
    },
    {
        "name": "发现-AI交通",
        "keywords": [
            "AI car", "autonomous driving", "self driving",
            "AI Tesla", "AI vehicle", "AI automotive",
            "AI drone", "AI aviation", "AI pilot",
            "AI navigation", "AI traffic", "AI transport",
            "AI delivery", "AI shipping", "AI fleet",
            "AI EV", "AI smart city", "AI mobility",
            "AI robotics vehicle", "AI lidar",
        ],
    },
    {
        "name": "发现-AI能源",
        "keywords": [
            "AI energy", "AI solar", "AI renewable",
            "AI power grid", "AI battery", "AI climate",
            "AI environment", "AI sustainability", "AI green",
            "AI oil gas", "AI mining", "AI nuclear",
            "AI smart grid", "AI carbon", "AI weather",
            "AI disaster", "AI ecology", "AI water",
            "AI agriculture tech", "AI food",
        ],
    },
    {
        "name": "发现-AI建筑",
        "keywords": [
            "AI architecture", "AI construction", "AI building",
            "AI real estate", "AI property", "AI urban",
            "AI smart home", "AI interior", "AI BIM",
            "AI engineering", "AI structural", "AI infrastructure",
            "AI city planning", "AI housing", "AI renovation",
            "AI landscape", "AI civil engineering", "AI materials",
            "AI sustainable building", "AI prop tech",
        ],
    },
    {
        "name": "发现-AI农业",
        "keywords": [
            "AI agriculture", "AI farming", "AI crop",
            "AI livestock", "AI agritech", "AI precision farming",
            "AI vertical farm", "AI greenhouse", "AI irrigation",
            "AI pest control", "AI soil", "AI harvest",
            "AI food tech", "AI restaurant", "AI kitchen",
            "AI recipe", "AI chef", "AI beverage",
            "AI nutrition tech", "AI food delivery",
        ],
    },
    {
        "name": "发现-AI艺术",
        "keywords": [
            "AI art", "generative art", "AI artist",
            "digital art AI", "AI creative", "AI imagination",
            "AI visual art", "AI sculpture", "AI museum",
            "AI gallery", "AI exhibition", "AI installation",
            "AI performance", "AI music video", "AI film",
            "AI documentary", "AI storytelling", "AI culture",
            "AI heritage", "AI NFT",
        ],
    },
    {
        "name": "发现-AI安全",
        "keywords": [
            "AI security", "AI cybersecurity", "AI defense",
            "AI military", "AI surveillance", "AI weapon",
            "AI threat detection", "AI hacking", "AI encryption",
            "AI privacy tech", "AI biometric", "AI facial recognition",
            "AI fraud detection", "AI risk management", "AI safety",
            "AI autonomous weapon", "AI warfare", "AI intelligence",
            "AI counterterrorism", "AI border",
        ],
    },
    {
        "name": "发现-AI语言",
        "keywords": [
            "AI language", "AI translation", "AI NLP",
            "natural language processing", "AI linguistics",
            "AI chatbot", "AI conversation", "AI speech",
            "AI voice", "AI text", "AI writing tool",
            "AI grammar", "AI dictionary", "AI multilingual",
            "AI subtitle", "AI dubbing", "AI transcription",
            "AI ASR", "AI TTS", "AI sentiment",
        ],
    },
    {
        "name": "发现-AI硬件",
        "keywords": [
            "AI chip", "AI GPU", "NVIDIA AI",
            "AI hardware", "AI processor", "AI server",
            "AI edge computing", "AI IoT", "AI sensor",
            "AI robot hardware", "AI drone hardware", "AI camera",
            "AI wearable", "AI device", "AI semiconductor",
            "AI memory", "AI storage", "AI networking",
            "AI quantum", "AI neuromorphic",
        ],
    },
    {
        "name": "发现-AI人力资源",
        "keywords": [
            "AI HR", "AI recruiting", "AI hiring",
            "AI talent", "AI workforce", "AI employee",
            "AI HR tech", "AI interview", "AI resume",
            "AI candidate", "AI onboarding", "AI training",
            "AI performance", "AI assessment", "AI coaching",
            "AI career", "AI job", "AI freelance",
            "AI gig economy", "AI remote work",
        ],
    },
    {
        "name": "发现-AI客户关系",
        "keywords": [
            "AI CRM", "AI customer", "AI support",
            "AI chatbot support", "AI helpdesk", "AI service",
            "AI feedback", "AI satisfaction", "AI experience",
            "AI engagement", "AI loyalty", "AI retention",
            "AI personalization", "AI recommendation", "AI user",
            "AI consumer", "AI buyer", "AI sales",
            "AI pipeline", "AI lead",
        ],
    },
    {
        "name": "发现-AI金融",
        "keywords": [
            "AI bank", "AI insurance", "AI fintech",
            "AI payment", "AI blockchain", "AI DeFi",
            "AI lending", "AI credit", "AI risk",
            "AI underwriting", "AI claim", "AI fraud",
            "AI compliance", "AI audit", "AI accounting",
            "AI tax", "AI wealth", "AI asset",
            "AI portfolio management", "AI financial planning",
        ],
    },
    {
        "name": "发现-AI教育技术",
        "keywords": [
            "AI edtech", "AI learning", "AI school",
            "AI university", "AI MOOC", "AI online course",
            "AI degree", "AI certification", "AI skill",
            "AI bootcamp", "AI academy", "AI institute",
            "AI research", "AI lab", "AI conference",
            "AI workshop", "AI tutorial", "AI course creator",
            "AI curriculum", "AI pedagogy",
        ],
    },
    {
        "name": "发现-AI空间",
        "keywords": [
            "AI space", "AI astronomy", "AI satellite",
            "AI NASA", "AI rocket", "AI aerospace",
            "AI exploration", "AI Mars", "AI Earth",
            "AI geospatial", "AI mapping", "AI GIS",
            "AI remote sensing", "AI climate monitoring",
            "AI weather forecast", "AI ocean", "AI geology",
            "AI planetary", "AI telescope", "AI cosmology",
        ],
    },
    {
        "name": "发现-AI体育",
        "keywords": [
            "AI sports", "AI fitness", "AI athlete",
            "AI coaching", "AI training", "AI performance",
            "AI analytics", "AI prediction", "AI betting",
            "AI esports", "AI gaming", "AI sport tech",
            "AI health monitor", "AI workout", "AI gym",
            "AI nutrition sport", "AI recovery", "AI injury",
            "AI scouting", "AI referee",
        ],
    },
    {
        "name": "发现-AI娱乐",
        "keywords": [
            "AI entertainment", "AI media", "AI streaming",
            "AI Netflix", "AI movie", "AI TV",
            "AI music production", "AI DJ", "AI podcast",
            "AI influencer", "AI celebrity", "AI fan",
            "AI social", "AI community", "AI meme",
            "AI comedy", "AI drama", "AI animation",
            "AI virtual idol", "AI VTuber",
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
        await session.commit()

    print(f"创建了 {len(TASKS)} 个新 CrawlerTask")
    print(f"总共 {sum(len(t['keywords']) for t in TASKS)} 个关键词")


if __name__ == "__main__":
    asyncio.run(main())
