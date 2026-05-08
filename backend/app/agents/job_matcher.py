"""
Job Matcher Agent
Reads master_jobs from Firestore, scores each against the user's
parsed ResumeProfile, and writes results to job_pool.

Scoring:
  - Skill overlap:   70% weight  (intersection / union of skills)
  - Seniority match: 30% weight  (exact=1.0, adjacent=0.6, mismatch=0.1)

Decision thresholds (from settings.match_threshold):
  - >= threshold + 0  → AUTO_APPLY  (Greenhouse ATS only)
  - >= threshold - 5  → MANUAL_REQUIRED
  - >= threshold - 15 → RECOMMENDATION
  - < threshold - 15  → skip (too weak)
"""
import uuid
from datetime import datetime, timezone

from app.db.firestore_client import get_db
from app.models.resume import ResumeProfile
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ATS types that support auto-apply
_AUTO_APPLY_ATS = {"GREENHOUSE"}

# Seniority ladder for proximity scoring
_SENIORITY_RANK = {
    "intern": 0, "junior": 1, "mid": 2,
    "senior": 3, "lead": 4, "principal": 5, "staff": 5,
}


def _seniority_score(profile_level: str, job_level: str) -> float:
    """Score 0.0–1.0 based on how close profile seniority is to job seniority."""
    p = _SENIORITY_RANK.get(profile_level.lower(), 2)
    j = _SENIORITY_RANK.get(job_level.lower(), 2)
    diff = abs(p - j)
    if diff == 0:
        return 1.0
    elif diff == 1:
        return 0.65
    elif diff == 2:
        return 0.30
    else:
        return 0.05


def _skill_overlap_score(profile_skills: list[str], job_skills: list[str]) -> float:
    """Jaccard-like overlap between profile and required skills (case-insensitive)."""
    if not job_skills:
        return 0.5  # no requirements specified — neutral
    profile_set = {s.lower() for s in profile_skills}
    job_set     = {s.lower() for s in job_skills}
    intersection = profile_set & job_set
    # Weight: intersection / required (not union) — missing skills penalise more
    return len(intersection) / len(job_set)


def _compute_score(profile: ResumeProfile, job: dict) -> float:
    """Return a 0–100 composite match score."""
    skill_s     = _skill_overlap_score(profile.skills, job.get("requiredSkills", []))
    seniority_s = _seniority_score(profile.seniority, job.get("seniority", "Mid"))
    raw = skill_s * 0.70 + seniority_s * 0.30
    return round(raw * 100, 1)


def _decide(score: float, ats_type: str, threshold: float) -> str | None:
    """Map score to decision string, or None if below minimum."""
    if score >= threshold and ats_type in _AUTO_APPLY_ATS:
        return "AUTO_APPLY"
    elif score >= threshold:
        return "MANUAL_REQUIRED"
    elif score >= threshold - 10:
        return "RECOMMENDATION"
    elif score >= threshold - 20:
        return "RECOMMENDATION"
    else:
        return None  # too weak — skip


def match_jobs_for_user(user_id: str, profile: ResumeProfile) -> int:
    """
    Main entry point. Called after resume parse or chat preference update.
    Reads master_jobs → filters by preferences → scores → writes to job_pool.
    Returns count of jobs written.
    """
    from app.db.user_profile import read_preferences
    
    db = get_db()
    threshold = settings.match_threshold   # default 92.0
    now = datetime.now(timezone.utc)
    
    # Load user preferences
    prefs = read_preferences(user_id) or {}
    pref_company = prefs.get("company", "").lower()
    pref_location = prefs.get("location", "").lower()
    pref_role = prefs.get("role", "").lower()

    # ── Load master jobs ──────────────────────────────────────
    master_docs = list(db.collection("master_jobs").stream())
    if not master_docs:
        logger.warning("No master_jobs found in Firestore. Run populate_master_jobs.py first.")
        return 0

    logger.info(f"Matching {len(master_docs)} master jobs for user {user_id}...")

    # ── Clear previous job_pool entries for this user ─────────
    old_jobs = (
        db.collection("job_pool")
        .where("userId", "==", user_id)
        .stream()
    )
    deleted = 0
    for doc in old_jobs:
        doc.reference.delete()
        deleted += 1
    if deleted:
        logger.info(f"Cleared {deleted} stale job_pool entries for {user_id}.")

    # ── Score and write ───────────────────────────────────────
    written = 0
    for doc in master_docs:
        job = doc.to_dict()
        
        # Apply Preferences Filter
        c_title = job.get("title", "").lower()
        c_comp  = job.get("company", "").lower()
        c_loc   = job.get("location", "").lower()
        
        if pref_company and pref_company not in c_comp:
            logger.debug(f"  Skip: {job.get('title')} @ {job.get('company')} — preference mismatch (company)")
            continue
        if pref_location and pref_location not in c_loc:
            logger.debug(f"  Skip: {job.get('title')} @ {job.get('company')} — preference mismatch (location)")
            continue
        if pref_role and pref_role not in c_title:
            logger.debug(f"  Skip: {job.get('title')} @ {job.get('company')} — preference mismatch (role)")
            continue

        score    = _compute_score(profile, job)
        ats_type = job.get("atsType", "UNKNOWN")
        decision = _decide(score, ats_type, threshold)

        if decision is None:
            logger.debug(f"  Skip: {job.get('title')} @ {job.get('company')} ({score}%) — below minimum")
            continue

        # Breakdown scores
        skill_s     = _skill_overlap_score(profile.skills, job.get("requiredSkills", []))
        seniority_s = _seniority_score(profile.seniority, job.get("seniority", "Mid"))

        matched_skills = [s for s in profile.skills if s.lower() in {r.lower() for r in job.get('requiredSkills', [])}]
        
        job_id = str(uuid.uuid4())
        payload = {
            "jobId":            job_id,
            "userId":           user_id,
            "title":            job.get("title", ""),
            "company":          job.get("company", ""),
            "location":         job.get("location", "Remote"),
            "package":          job.get("package", "Competitive"),
            "url":              job.get("url", ""),
            "atsType":          ats_type,
            "matchScore":       score,
            "vectorScore":      round(skill_s * 100, 1),
            "reasoningScore":   round(seniority_s * 100, 1),
            "decision":         decision,
            "reasoningSummary": (
                f"Skill overlap: {round(skill_s*100)}% | "
                f"Seniority match: {job.get('seniority', '?')} vs {profile.seniority}. "
                f"Matched skills: {', '.join(matched_skills[:5])}."
            ),
            "descriptionRaw":   job.get("descriptionRaw", "")[:2000],
            "discoveredAt":     now,
            "updatedAt":        now,
        }
        db.collection("job_pool").document(job_id).set(payload)
        written += 1
        logger.info(
            f"  [{decision[:4]}] {job.get('title')} @ {job.get('company')} | {score}%"
        )

    logger.info(f"Job matching complete: {written}/{len(master_docs)} jobs written to job_pool.")
    return written
