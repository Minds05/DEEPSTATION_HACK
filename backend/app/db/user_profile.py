"""
Firestore CRUD — users/{userId}/profile & preferences
Admin SDK — bypasses security rules (full trust).
"""
from datetime import datetime, timezone
from typing import Optional

from app.db.firestore_client import get_db
from app.models.resume import ResumeProfile
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ── Profile ───────────────────────────────────────────────────

def write_profile(user_id: str, profile: ResumeProfile) -> None:
    """Write (upsert) the parsed resume profile to Firestore."""
    db = get_db()
    doc_ref = db.collection("users").document(user_id).collection("profile").document("data")
    payload = profile.model_dump()
    payload["parsed_at"] = datetime.now(timezone.utc)
    doc_ref.set(payload)
    logger.info(f"Profile written for user={user_id} | skills={len(profile.skills)} | seniority={profile.seniority}")


def read_profile(user_id: str) -> Optional[dict]:
    """Read the user's profile from Firestore. Returns None if not found."""
    db = get_db()
    doc = db.collection("users").document(user_id).collection("profile").document("data").get()
    if doc.exists:
        return doc.to_dict()
    logger.warning(f"Profile not found for user={user_id}")
    return None


def update_resume_url(user_id: str, resume_url: str) -> None:
    """Update only the resume_url field after Firebase Storage upload."""
    db = get_db()
    db.collection("users").document(user_id)\
      .collection("profile").document("data")\
      .update({"resume_url": resume_url})
    logger.info(f"resume_url updated for user={user_id}")


# ── Preferences ───────────────────────────────────────────────

def write_preferences(user_id: str, preferences: dict) -> None:
    """Write user job search preferences."""
    db = get_db()
    preferences["updated_at"] = datetime.now(timezone.utc)
    db.collection("users").document(user_id)\
      .collection("preferences").document("data")\
      .set(preferences, merge=True)
    logger.info(f"Preferences written for user={user_id}")


def read_preferences(user_id: str) -> Optional[dict]:
    """Read job search preferences. Returns None if not set."""
    db = get_db()
    doc = db.collection("users").document(user_id)\
             .collection("preferences").document("data").get()
    return doc.to_dict() if doc.exists else None


# ── Task Status ───────────────────────────────────────────────

def write_task_status(user_id: str, status_data: dict) -> None:
    """Upsert orchestrator task_status heartbeat."""
    db = get_db()
    status_data["updated_at"] = datetime.now(timezone.utc)
    db.collection("users").document(user_id)\
      .collection("task_status").document("current")\
      .set(status_data, merge=True)
