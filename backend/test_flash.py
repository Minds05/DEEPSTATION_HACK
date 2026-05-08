import asyncio
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv(override=True)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

async def test():
    try:
        model = genai.GenerativeModel("gemini-flash-latest")
        r = await model.generate_content_async("Say WORKING")
        print("Success gemini-flash-latest!", r.text)
    except Exception as e:
        print(f"Failed gemini-flash-latest: {e}")

asyncio.run(test())
