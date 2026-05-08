"""
Applications DB — Firestore CRUD for applications/{appId} collection.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.db.firestore_client import get_db
from app.models.application import ApplicationRecord, AppStatus
from app.utils.logger import get_logger

logger = get_logger(__name__)

_COLLECTION = "applications"


def create_application(record: ApplicationRecord) -> str:
    """
    Write a new application record to Firestore.
    Returns the app_id (Firestore document ID).
    """
    db = get_db()
    app_id = record.app_id or str(uuid.uuid4())

    payload = {
        "appId":           app_id,
        "jobId":           record.job_id,
        "userId":          record.user_id,
        "status":          record.status.value,
        "matchScore":      round(record.match_score, 2),
        "atsType":         record.ats_type,
        "timestamp":       record.timestamp or datetime.now(timezone.utc),
        "screenshotUrl":   record.screenshot_url,
        "coverLetter":     None,          # PII guard — cover letter stored separately
        "coverLetterUrl":  record.cover_letter_url,
        "errorLog":        record.error_log,
    }

    db.collection(_COLLECTION).document(app_id).set(payload)
    logger.info(
        f"Application created: appId={app_id} jobId={record.job_id} "
        f"status={record.status.value} score={record.match_score:.1f}%"
    )
    return app_id


def update_application_status(
    app_id: str,
    status: AppStatus,
    screenshot_url: Optional[str] = None,
    error_log: Optional[str] = None,
) -> None:
    """Update only the status (and optionally screenshot/error) of an application."""
    db = get_db()
    update = {
        "status": status.value,
        "updatedAt": datetime.now(timezone.utc),
    }
    if screenshot_url:
        update["screenshotUrl"] = screenshot_url
    if error_log:
        update["errorLog"] = error_log

    db.collection(_COLLECTION).document(app_id).update(update)
    logger.info(f"Application {app_id} → {status.value}")


def read_application(app_id: str) -> Optional[dict]:
    """Read a single application by ID."""
    db = get_db()
    doc = db.collection(_COLLECTION).document(app_id).get()
    return doc.to_dict() if doc.exists else None


def list_applications(user_id: str, limit: int = 50) -> list[dict]:
    """Return all applications for a user, newest first."""
    db = get_db()
    docs = (
        db.collection(_COLLECTION)
        .where("userId", "==", user_id)
        .order_by("timestamp", direction="DESCENDING")
        .limit(limit)
        .stream()
    )
    return [{"appId": d.id, **d.to_dict()} for d in docs]
