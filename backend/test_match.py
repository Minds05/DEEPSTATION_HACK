import asyncio
from app.db.firestore_client import init_firestore
from app.agents.job_matcher import match_jobs_for_user
from app.models.resume import ResumeProfile

init_firestore()

# Mock the user profile that was saved to firestore
from app.db.user_profile import read_profile
profile_dict = read_profile("google-deepstation")
if profile_dict:
    profile = ResumeProfile(**profile_dict)
    print(f"Profile: {profile.skills}")
    matched = match_jobs_for_user("google-deepstation", profile)
    print(f"Matched {matched} jobs.")
else:
    print("No profile found")
