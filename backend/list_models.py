import os, sys
sys.path.insert(0, ".")
from dotenv import load_dotenv
from pathlib import Path

# Load root .env
root_env = Path(__file__).parent.parent / ".env"
load_dotenv(root_env)

api_key = os.getenv("GEMINI_API_KEY", "")
if not api_key:
    print("ERROR: GEMINI_API_KEY not set")
    sys.exit(1)

import google.generativeai as genai
genai.configure(api_key=api_key)

print(f"SDK version: {genai.__version__}")
print("\nAvailable models supporting generateContent:")
for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(f"  {m.name}")
