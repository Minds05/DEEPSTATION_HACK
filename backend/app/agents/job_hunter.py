"""
Job Hunter Agent — Google Search Grounding via Gemini 2.0 Flash

Builds targeted queries for Lever and Greenhouse job boards,
fetches live results using Gemini's search grounding capability,
and extracts structured JobListing objects from the results.
"""
import asyncio
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.models.job import JobListing, ATSType
from app.models.resume import ResumeProfile
from app.browser.ats_guard import detect_ats
from app.utils.logger import get_logger

logger = get_logger(__name__)
genai.configure(api_key=settings.gemini_api_key)


# ── Query builder ─────────────────────────────────────────────

def build_search_queries(
    profile: ResumeProfile,
    role: Optional[str] = None,
    location: Optional[str] = None,
    remote: bool = False,
) -> list[str]:
    """
    Build a targeted list of Google search queries.
    Prioritises Lever and Greenhouse ATS URLs.
    """
    top_skills = " ".join(profile.skills[:4]) if profile.skills else ""
    role_term  = role or _infer_role(profile)
    loc_term   = "remote" if remote else (location or "")

    queries = []

    # Primary: Lever + Greenhouse targeted queries
    for site in ["site:jobs.lever.co", "site:boards.greenhouse.io"]:
        q = f'{site} "{role_term}"'
        if loc_term:
            q += f' "{loc_term}"'
        queries.append(q)

    # Broader skill-based query
    broad = f'"{role_term}" {top_skills} jobs'
    if loc_term:
        broad += f' "{loc_term}"'
    broad += " site:lever.co OR site:greenhouse.io"
    queries.append(broad)

    # Seniority-scoped query
    seniority_map = {
        "Lead": "Staff OR Lead OR Principal",
        "Senior": "Senior OR Sr.",
        "Mid": "Software Engineer OR Developer",
        "Junior": "Junior OR Associate",
    }
    seniority_qualifier = seniority_map.get(profile.seniority, "")
    if seniority_qualifier:
        queries.append(
            f'{seniority_qualifier} "{role_term}" jobs {top_skills} '
            f'site:lever.co OR site:greenhouse.io'
        )

    logger.info(f"Built {len(queries)} search queries for role='{role_term}'")
    return queries[:4]  # Cap at 4 queries per hunt


def _infer_role(profile: ResumeProfile) -> str:
    """Infer best-fit role from skills if user didn't specify."""
    skill_set = {s.lower() for s in profile.skills}
    if any(k in skill_set for k in ("pytorch", "tensorflow", "llm", "mlops", "machine learning", "ml")):
        return "AIML Engineer"
    if any(k in skill_set for k in ("react", "vue", "angular", "frontend", "next.js")):
        return "Frontend Engineer"
    if any(k in skill_set for k in ("fastapi", "django", "node.js", "backend", "api")):
        return "Backend Engineer"
    if any(k in skill_set for k in ("kubernetes", "terraform", "devops", "gcp", "aws")):
        return "DevOps Engineer"
    return "Software Engineer"


# ── Grounded search ───────────────────────────────────────────

_EXTRACT_PROMPT = """
You are given a search query result page about job listings.
Extract all distinct job listings from the content below.

Return ONLY a valid JSON array — no markdown, no explanation:
[
  {{
    "title": "Job Title",
    "company": "Company Name",
    "url": "https://full-direct-application-url.com",
    "description": "Brief job description or requirements (2-4 sentences)"
  }}
]

Rules:
- Only include listings where the URL is a direct application/job page (not a search result).
- If you cannot find any listings, return an empty array: []
- URLs must be complete (include https://).
- Extract at most 8 listings.

Content:
{content}
"""


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=6))
async def _search_with_grounding(query: str) -> list[dict]:
    """
    Run a single Gemini grounded search and extract job listings.
    Uses google_search tool for live web results.
    """
    model = genai.GenerativeModel(
        model_name=settings.gemini_model,
        tools='google_search_retrieval',
    )

    # Step 1: Grounded search to get live content
    search_response = await model.generate_content_async(
        f"Search for job listings: {query}",
        generation_config={"temperature": 0},
    )

    # Step 2: Extract grounding metadata / text
    grounded_text = search_response.text or ""

    # Also pull search grounding chunks if available
    try:
        candidates = search_response.candidates
        if candidates and candidates[0].grounding_metadata:
            chunks = candidates[0].grounding_metadata.grounding_chunks
            for chunk in chunks[:5]:
                if hasattr(chunk, 'web') and chunk.web:
                    grounded_text += f"\nURL: {chunk.web.uri}\nTitle: {chunk.web.title}\n"
    except Exception:
        pass  # grounding metadata is optional

    if not grounded_text.strip():
        return []

    # Step 3: Extract structured listings from grounded content
    extract_model = genai.GenerativeModel(settings.gemini_model)
    extract_response = await extract_model.generate_content_async(
        _EXTRACT_PROMPT.format(content=grounded_text[:6000]),
        generation_config={"temperature": 0},
    )

    return _parse_listings_json(extract_response.text)


def _parse_listings_json(text: str) -> list[dict]:
    """Parse the JSON array of job listings from Gemini's response."""
    try:
        text = re.sub(r'```(?:json)?\s*', '', text).strip().rstrip('`').strip()
        start = text.find('[')
        end   = text.rfind(']')
        if start == -1 or end == -1:
            return []
        import json
        data = json.loads(text[start:end + 1])
        return data if isinstance(data, list) else []
    except Exception as e:
        logger.warning(f"Failed to parse listings JSON: {e}")
        return []


# ── Main hunt function ────────────────────────────────────────

async def hunt_jobs(
    profile: ResumeProfile,
    role: Optional[str] = None,
    location: Optional[str] = None,
    remote: bool = False,
) -> list[JobListing]:
    """
    Execute parallel grounded searches across all query variants.
    Deduplicates by URL and returns structured JobListing objects.
    """
    queries = build_search_queries(profile, role, location, remote)

    # Run all queries concurrently
    search_tasks = [_search_with_grounding(q) for q in queries]
    results_per_query = await asyncio.gather(*search_tasks, return_exceptions=True)

    # Flatten + deduplicate by URL
    seen_urls: set[str] = set()
    listings: list[JobListing] = []

    for result in results_per_query:
        if isinstance(result, Exception):
            logger.warning(f"Search query failed: {result}")
            continue
        for item in result:
            url = item.get("url", "").strip()
            if not url or url in seen_urls:
                continue
            if not url.startswith("http"):
                continue
            seen_urls.add(url)

            ats_type = detect_ats(url)
            listings.append(JobListing(
                job_id=str(uuid.uuid4()),
                title=item.get("title", "Unknown Role"),
                company=item.get("company", "Unknown Company"),
                url=url,
                description_raw=item.get("description", ""),
                ats_type=ats_type,
                discovered_at=datetime.now(timezone.utc),
            ))

    logger.info(f"Hunt complete: {len(listings)} unique jobs found across {len(queries)} queries")
    return listings
