"""
Scorer — 92% Threshold Decision Matrix

Scoring breakdown:
  40% → Vector Match   (Gemini text-embedding-004 cosine similarity)
  60% → Reasoning Match (Gemini 2.0 Flash structured evaluation)

Decision routing:
  score >= 92 AND (Lever OR Greenhouse) → AUTO_APPLY
  score >= 92 AND (Workday OR Other)    → MANUAL_REQUIRED
  score < 92                            → RECOMMENDATION
"""
import math
import json
import re
from typing import Optional

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.models.job import ATSType, Decision, MatchResult
from app.models.resume import ResumeProfile
from app.browser.ats_guard import is_auto_apply_eligible
from app.utils.logger import get_logger

logger = get_logger(__name__)

genai.configure(api_key=settings.gemini_api_key)

_EMBEDDING_MODEL = "models/text-embedding-004"

# ── Reasoning evaluation prompt ───────────────────────────────
_REASONING_PROMPT = """
You are a senior technical recruiter. Evaluate how well the candidate profile matches the job description.

Return ONLY a valid JSON object — no markdown, no explanation:
{{
  "score": <integer 0-100>,
  "summary": "<2-3 sentence honest assessment>"
}}

Scoring criteria:
- Technical skill overlap with JD requirements (40 pts)
- Seniority and years-of-experience alignment (25 pts)
- Domain/industry relevance (20 pts)
- Project impact alignment with role expectations (15 pts)

Be strict. A score of 92+ means the candidate is a near-perfect fit.
A score of 70-91 means strong but missing something critical.
Below 70 means significant gaps.

--- CANDIDATE PROFILE ---
Name: {name}
Seniority: {seniority}
Years Experience: {yoe}
Skills: {skills}
Top Projects:
{projects}

--- JOB DESCRIPTION ---
Title: {title}
Company: {company}
Description:
{jd_text}
"""


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two embedding vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a ** 2 for a in vec_a))
    mag_b = math.sqrt(sum(b ** 2 for b in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _build_profile_text(profile: ResumeProfile) -> str:
    """Flatten profile into a single text block for embedding."""
    parts = [
        f"Seniority: {profile.seniority}",
        f"Skills: {', '.join(profile.skills)}",
    ]
    for proj in profile.projects[:3]:
        parts.append(
            f"Project: {proj.title} — {proj.description} | "
            f"Impact: {proj.impact} | Tech: {', '.join(proj.technologies)}"
        )
    return "\n".join(parts)


def _extract_json_block(text: str) -> str:
    """Strip markdown fences and extract JSON object."""
    text = re.sub(r'```(?:json)?\s*', '', text).strip().rstrip('`').strip()
    start, end = text.find('{'), text.rfind('}')
    if start == -1 or end == -1:
        raise ValueError(f"No JSON in response: {text[:200]}")
    return text[start:end + 1]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
async def _get_embedding(text: str) -> list[float]:
    """Fetch a Gemini text embedding vector."""
    result = genai.embed_content(
        model=_EMBEDDING_MODEL,
        content=text,
        task_type="RETRIEVAL_QUERY",
    )
    return result["embedding"]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
async def _get_reasoning_score(
    profile: ResumeProfile,
    job_title: str,
    job_company: str,
    jd_text: str,
) -> tuple[float, str]:
    """
    Ask Gemini 2.0 Flash to reason about the profile-JD fit.
    Returns (score_0_to_100, summary_text).
    """
    model = genai.GenerativeModel(settings.gemini_model)

    projects_text = "\n".join(
        f"  - {p.title}: {p.description} | Impact: {p.impact}"
        for p in profile.projects[:3]
    ) or "  - No projects listed."

    prompt = _REASONING_PROMPT.format(
        name=profile.name,
        seniority=profile.seniority,
        yoe=profile.years_experience or "unknown",
        skills=", ".join(profile.skills[:20]),
        projects=projects_text,
        title=job_title,
        company=job_company,
        jd_text=jd_text[:3000],   # token guard
    )

    response = await model.generate_content_async(prompt)
    raw = _extract_json_block(response.text)
    data = json.loads(raw)

    score = float(data.get("score", 0))
    summary = data.get("summary", "No assessment available.")
    return score, summary


async def score_job(
    profile: ResumeProfile,
    job_title: str,
    job_company: str,
    job_url: str,
    jd_text: str,
    ats_type: ATSType,
    job_id: str,
) -> MatchResult:
    """
    Full 40/60 scoring pipeline.

    1. Embed profile text + JD → cosine similarity → vector_score (0-100)
    2. Gemini Flash reasoning → reasoning_score (0-100)
    3. Combined = 0.4 * vector + 0.6 * reasoning
    4. Apply 92% threshold decision logic
    """
    logger.info(f"Scoring: {job_title} @ {job_company}")

    # ── Step 1: Vector Score (40%) ────────────────────────────
    try:
        profile_text = _build_profile_text(profile)
        profile_vec = await _get_embedding(profile_text)
        jd_vec = await _get_embedding(jd_text[:4000])
        raw_cosine = _cosine_similarity(profile_vec, jd_vec)
        # Cosine similarity → scale to 0-100
        # Gemini embeddings are well-calibrated; typical range 0.6–0.95 for related content
        vector_score = round(min(max(raw_cosine * 110, 0), 100), 2)
    except Exception as e:
        logger.warning(f"Embedding failed (using fallback 50): {e}")
        vector_score = 50.0

    # ── Step 2: Reasoning Score (60%) ─────────────────────────
    try:
        reasoning_raw, reasoning_summary = await _get_reasoning_score(
            profile, job_title, job_company, jd_text
        )
        reasoning_score = round(min(max(float(reasoning_raw), 0), 100), 2)
    except Exception as e:
        logger.warning(f"Reasoning score failed (using fallback 50): {e}")
        reasoning_score = 50.0
        reasoning_summary = "Scoring unavailable — API error."

    # ── Step 3: Combined Score ─────────────────────────────────
    combined = round((0.4 * vector_score) + (0.6 * reasoning_score), 2)

    # ── Step 4: Decision Routing ───────────────────────────────
    threshold = settings.match_threshold  # 92.0
    if combined >= threshold:
        if is_auto_apply_eligible(ats_type):
            decision = Decision.AUTO_APPLY
        else:
            decision = Decision.MANUAL_REQUIRED
    else:
        decision = Decision.RECOMMENDATION

    logger.info(
        f"Score result: vector={vector_score:.1f} reasoning={reasoning_score:.1f} "
        f"combined={combined:.1f} → {decision.value}"
    )

    return MatchResult(
        job_id=job_id,
        match_score=combined,
        vector_score=vector_score,
        reasoning_score=reasoning_score,
        reasoning_summary=reasoning_summary,
        decision=decision,
    )
