from app.config import settings
k = settings.gemini_api_key
print(f"Key (first 12): {k[:12]}...{k[-4:]}")
print(f"Model         : {settings.gemini_model}")
print(f"User ID       : {settings.user_id}")
