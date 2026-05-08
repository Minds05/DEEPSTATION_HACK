"""
Job Pool — Firestore CRUD for job_pool/{jobId} collection.
Admin SDK — bypasses security rules.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.db.firestore_client import get_db
from app.models.job import JobListing, MatchResult, Decision
from app.utils.logger import get_logger

logger = get_logger(__name__)

_COLLECTION = "job_pool"


def write_job(listing: JobListing, match: MatchResult, user_id: str) -> str:
    """
    Upsert a job listing + match result into job_pool.
    Returns the job_id (Firestore document ID).
    """
    db = get_db()
    job_id = listing.job_id or str(uuid.uuid4())

    payload = {
        # Listing fields
        "jobId":          job_id,
        "title":          listing.title,
        "company":        listing.company,
        "url":            listing.url,
        "atsType":        listing.ats_type.value,
        "descriptionRaw": listing.description_raw[:4000],   # trim for Firestore limits
        "discoveredAt":   listing.discovered_at or datetime.now(timezone.utc),
        "userId":         user_id,
        # Scoring fields
        "matchScore":        round(match.match_score, 2),
        "vectorScore":       round(match.vector_score, 2),
        "reasoningScore":    round(match.reasoning_score, 2),
        "reasoningSummary":  match.reasoning_summary,
        "decision":          match.decision.value,
        # Meta
        "updatedAt": datetime.now(timezone.utc),
    }

    db.collection(_COLLECTION).document(job_id).set(payload, merge=True)
    logger.info(
        f"Job written: {listing.title} @ {listing.company} | "
        f"score={match.match_score:.1f}% | decision={match.decision.value}"
    )
    return job_id


def read_job(job_id: str) -> Optional[dict]:
    """Read a single job from job_pool."""
    db = get_db()
    doc = db.collection(_COLLECTION).document(job_id).get()
    return doc.to_dict() if doc.exists else None


def list_jobs(user_id: str, limit: int = 50) -> list[dict]:
    """
    Return all jobs for a user, sorted by matchScore descending.
    """
    db = get_db()
    docs = (
        db.collection(_COLLECTION)
        .where("userId", "==", user_id)
        .order_by("matchScore", direction="DESCENDING")
        .limit(limit)
        .stream()
    )
    return [{"jobId": d.id, **d.to_dict()} for d in docs]


def list_jobs_by_decision(user_id: str, decision: Decision) -> list[dict]:
    """Filter jobs by decision type (AUTO_APPLY / MANUAL_REQUIRED / RECOMMENDATION)."""
    db = get_db()
    docs = (
        db.collection(_COLLECTION)
        .where("userId", "==", user_id)
        .where("decision", "==", decision.value)
        .order_by("matchScore", direction="DESCENDING")
        .stream()
    )
    return [{"jobId": d.id, **d.to_dict()} for d in docs]


def delete_job(job_id: str) -> None:
    """Remove a job from the pool (admin only)."""
    get_db().collection(_COLLECTION).document(job_id).delete()
    logger.info(f"Job deleted: {job_id}")
