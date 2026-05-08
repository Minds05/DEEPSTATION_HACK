"""
Thought Log CRUD — writes Zone B activity feed entries to Firestore.
All messages are PII-scrubbed by the logger before writing.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.db.firestore_client import get_db
from app.utils.logger import get_logger, scrub_pii

logger = get_logger(__name__)


def write_thought_log(
    user_id: str,
    message: str,
    log_type: str = "Thought",
    job_id: Optional[str] = None,
    app_id: Optional[str] = None,
) -> str:
    """
    Write a single thought log entry to Firestore thought_logs collection.
    PII is scrubbed from the message before writing.
    Returns the log_id.
    """
    log_id = str(uuid.uuid4())
    safe_message = scrub_pii(message)

    payload = {
        "userId": user_id,
        "type": log_type,        # Thought | Action | Warning | Error | Success
        "message": safe_message,
        "timestamp": datetime.now(timezone.utc),
    }
    if job_id:
        payload["jobId"] = job_id
    if app_id:
        payload["appId"] = app_id

    get_db().collection("thought_logs").document(log_id).set(payload)
    logger.info(f"[{log_type}] {safe_message}")
    return log_id


def get_recent_logs(user_id: str, limit: int = 50) -> list[dict]:
    """Fetch the most recent thought logs for a user."""
    db = get_db()
    docs = (
        db.collection("thought_logs")
        .where("userId", "==", user_id)
        .order_by("timestamp", direction="DESCENDING")
        .limit(limit)
        .stream()
    )
    return [{"log_id": d.id, **d.to_dict()} for d in docs]
