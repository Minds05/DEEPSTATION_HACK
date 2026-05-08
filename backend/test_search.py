import asyncio
import google.generativeai as genai
from app.config import settings
import warnings
warnings.filterwarnings("ignore")

genai.configure(api_key=settings.gemini_api_key)

async def test():
    try:
        model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            tools='google_search_retrieval'
        )
        r = await model.generate_content_async("What is the current price of AAPL?")
        print("Success with 'google_search_retrieval'!")
    except Exception as e:
        print(f"Failed with 'google_search_retrieval': {e}")

asyncio.run(test())
