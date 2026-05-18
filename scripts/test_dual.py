import asyncio
import sys
sys.path.insert(0, r"D:\Projects\YouTube\tubefactory-ocp")
from apps.api.config import settings
from apps.api.services.youtube_api import DualTrackExtractor

extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)

async def test():
    for kw in ['Pika Labs', 'Runway tutorial', 'Sora OpenAI']:
        try:
            result = await extractor._api.search_list(kw, max_results=5, search_type='channel')
            print(f"{kw}: ok, {len(result.get('items', []))} items")
        except Exception as e:
            print(f"{kw}: FAILED {type(e).__name__}: {e}")

asyncio.run(test())
