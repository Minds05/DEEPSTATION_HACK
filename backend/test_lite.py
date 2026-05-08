import asyncio
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv(override=True)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

async def test():
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        r = await model.generate_content_async("Say WORKING")
        print("Success 2.0-flash-lite!", r.text)
    except Exception as e:
        print(f"Failed 2.0-flash-lite: {e}")

asyncio.run(test())
