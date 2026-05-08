"""
Resume Parser Agent
Uses Gemini 2.0 Flash to extract structured profile data from raw resume text.
Returns a validated ResumeProfile Pydantic model.
"""
import json
import re
from tenacity import retry, stop_after_attempt, wait_exponential

import google.generativeai as genai

from app.config import settings
from app.models.resume import ResumeProfile, Project, Education
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Configure Gemini ──────────────────────────────────────────
genai.configure(api_key=settings.gemini_api_key)


_EXTRACTION_PROMPT = """
You are an expert technical resume analyst. Extract structured information from the resume text below.

Return ONLY a valid JSON object — no markdown fences, no explanation, just pure JSON — with this exact schema:
{{
  "name": "Full Name",
  "linkedin_url": "https://linkedin.com/in/... or null",
  "skills": ["Python", "FastAPI", "React", ...],
  "seniority": "Junior | Mid | Senior | Lead | Principal",
  "years_experience": 4.5,
  "projects": [
    {{
      "title": "Project Name",
      "description": "What it does",
      "impact": "Quantified outcome (e.g., reduced latency by 40%)",
      "technologies": ["Python", "GCP"]
    }}
  ],
  "education": [
    {{
      "degree": "B.Tech Computer Science",
      "institution": "IIT Bombay",
      "year": 2021
    }}
  ]
}}

Rules:
- skills: Extract ALL technical skills (languages, frameworks, tools, cloud platforms, ML/AI).
- seniority: Infer from YoE + job titles (0-2=Junior, 3-5=Mid, 6-9=Senior, 10+=Lead/Principal).
- years_experience: Calculate from earliest role to present. Use null if not determinable.
- projects: Include top 3-5 most impactful. Focus on measurable outcomes.
- If a field is truly absent, use null for scalar fields and [] for arrays.

Resume Text:
---
{resume_text}
---
"""

_AUDIT_PROMPT = """
You are a no-nonsense career coach AI (C-IAW). Based on the parsed resume profile below,
generate a short, direct opening audit message (2-3 sentences) to send to the user in a chat.

Format:
- Start with: "I've mapped your profile."
- Call out their TOP 2 strongest skills explicitly.
- Flag 1 key gap or weakness (be direct, not diplomatic).
- End with a question: ask whether to prioritize a specific location or focus on role type regardless of geography.

Profile:
{profile_json}

Return only the message text. No labels, no quotes.
"""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def parse_resume(raw_text: str) -> ResumeProfile:
    """
    Send resume text to Gemini 2.0 Flash and extract a structured ResumeProfile.
    Retries up to 3 times on transient API failures.
    """
    model = genai.GenerativeModel(settings.gemini_model)

    prompt = _EXTRACTION_PROMPT.format(resume_text=raw_text[:12000])  # token guard

    logger.info("Sending resume text to Gemini for extraction...")
    response = await model.generate_content_async(prompt)

    raw_json = _extract_json(response.text)
    data = json.loads(raw_json)

    profile = ResumeProfile(
        name=data.get("name", "Unknown"),
        linkedin_url=data.get("linkedin_url"),
        skills=data.get("skills", []),
        seniority=data.get("seniority", "Mid"),
        years_experience=data.get("years_experience"),
        projects=[Project(**p) for p in data.get("projects", [])],
        education=[Education(**e) for e in data.get("education", [])],
    )

    logger.info(
        f"Parsed profile: name={profile.name} | seniority={profile.seniority} "
        f"| skills={len(profile.skills)} | projects={len(profile.projects)}"
    )
    return profile


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5))
async def generate_audit_message(profile: ResumeProfile) -> str:
    """
    Generate the Zone A opening chat message — a direct coach-style audit.
    Called immediately after resume parsing, before job search begins.
    """
    model = genai.GenerativeModel(settings.gemini_model)
    profile_json = profile.model_dump_json(indent=2)
    prompt = _AUDIT_PROMPT.format(profile_json=profile_json)

    response = await model.generate_content_async(prompt)
    audit_msg = response.text.strip()
    logger.info("Audit message generated.")
    return audit_msg


def _extract_json(text: str) -> str:
    """
    Strip markdown fences and isolate the JSON object from Gemini's response.
    Handles ```json ... ``` and raw JSON.
    """
    # Remove markdown code fences
    text = re.sub(r'```(?:json)?\s*', '', text).strip().rstrip('`').strip()
    # Find the outermost { ... }
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in Gemini response: {text[:200]}")
    return text[start:end + 1]
