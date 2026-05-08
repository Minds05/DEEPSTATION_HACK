"""Quick Gemini API key + model test — run from backend/ directory."""
import os, sys, asyncio
from pathlib import Path

# ── Force-load root .env (override=True ignores system env vars) ──
from dotenv import load_dotenv

root_env   = Path(__file__).resolve().parent.parent / ".env"
backend_env = Path(__file__).resolve().parent / ".env"

print(f"Loading .env from: {root_env}")
print(f"Root .env exists : {root_env.exists()}")
print(f"Backend .env exists: {backend_env.exists()}")

# Load with override=True so file values always win over system env vars
loaded = load_dotenv(root_env, override=True)
print(f"Loaded           : {loaded}")

api_key = os.getenv("GEMINI_API_KEY", "")
model   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

print(f"\nAPI Key (first 16): {api_key[:16]}...")
print(f"API Key (last 4)  : ...{api_key[-4:]}")
print(f"Model             : {model}")

if not api_key or "PASTE" in api_key:
    print("\nERROR: API key is placeholder. Update .env line 13 first.")
    sys.exit(1)

import google.generativeai as genai
genai.configure(api_key=api_key)

async def test():
    try:
        m = genai.GenerativeModel(model)
        r = await m.generate_content_async("Say the word: WORKING")
        print(f"\nSUCCESS: {r.text.strip()}")
    except Exception as e:
        print(f"\nFAILED: {e}")

asyncio.run(test())
