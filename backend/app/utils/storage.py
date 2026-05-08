"""
Storage Helper — Firebase Storage with local disk fallback.

Firebase Storage requires the Blaze (paid) plan.
If Storage is unavailable, files are saved to backend/uploads/
and a local file:// URL is returned.  Everything else (Gemini
parsing, Firestore, auto-apply) works identically either way.
"""
import io
import uuid
import os
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Local fallback directory — career-agent/backend/uploads/
_UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"


def _local_save(rel_path: str, data: bytes, content_type: str = "") -> str:
    """Save bytes to local disk and return a file:// URL."""
    full_path = _UPLOAD_DIR / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(data)
    logger.info(f"[LocalStorage] Saved to {full_path}")
    return full_path.as_uri()          # file:///...absolute path...


def _try_get_bucket():
    """Return Firebase Storage bucket, or None if unavailable."""
    try:
        from app.db.firestore_client import get_bucket
        return get_bucket()
    except Exception:
        return None


def upload_resume(user_id: str, pdf_bytes: bytes, filename: str) -> str:
    """
    Upload a resume PDF.
    Tries Firebase Storage first; falls back to local disk.
    Returns the download URL (public GCS URL or local file:// path).
    """
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    blob_path   = f"resumes/{user_id}/{unique_name}"

    bucket = _try_get_bucket()
    if bucket:
        try:
            blob = bucket.blob(blob_path)
            blob.upload_from_string(pdf_bytes, content_type="application/pdf")
            blob.make_public()
            url = blob.public_url
            logger.info(f"Resume uploaded to Firebase Storage: {blob_path}")
            return url
        except Exception as e:
            logger.warning(f"Firebase Storage upload failed ({e}). Using local fallback.")

    # ── Local fallback ────────────────────────────────────────
    return _local_save(blob_path, pdf_bytes, "application/pdf")


def upload_screenshot(user_id: str, app_id: str, image_bytes: bytes) -> str:
    """Upload auto-apply screenshot. Falls back to local disk."""
    blob_path = f"screenshots/{user_id}/{app_id}.png"

    bucket = _try_get_bucket()
    if bucket:
        try:
            blob = bucket.blob(blob_path)
            blob.upload_from_string(image_bytes, content_type="image/png")
            blob.make_public()
            logger.info(f"Screenshot uploaded to Firebase Storage: {blob_path}")
            return blob.public_url
        except Exception as e:
            logger.warning(f"Firebase Storage screenshot failed ({e}). Using local fallback.")

    return _local_save(blob_path, image_bytes, "image/png")


def upload_cover_letter(user_id: str, app_id: str, pdf_bytes: bytes) -> str:
    """Upload cover letter PDF. Falls back to local disk."""
    blob_path = f"covers/{user_id}/{app_id}.pdf"

    bucket = _try_get_bucket()
    if bucket:
        try:
            blob = bucket.blob(blob_path)
            blob.upload_from_string(pdf_bytes, content_type="application/pdf")
            blob.make_public()
            logger.info(f"Cover letter uploaded to Firebase Storage: {blob_path}")
            return blob.public_url
        except Exception as e:
            logger.warning(f"Firebase Storage cover letter failed ({e}). Using local fallback.")

    return _local_save(blob_path, pdf_bytes, "application/pdf")
