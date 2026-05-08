"""
Firestore Admin SDK client — singleton init.
Backend uses Admin SDK (bypasses security rules — full trust).
"""
import firebase_admin
from firebase_admin import credentials, firestore, storage

from app.config import settings

_db = None
_bucket = None


def _resolve_sa_path(raw: str) -> str:
    """
    Resolve the service account JSON path to an absolute path.
    - If the configured path is already absolute → use it as-is.
    - If relative (e.g. './firebase-service-account.json') →
      resolve it relative to the backend/ directory
      (two levels up from this file: db/ → app/ → backend/).
    """
    from pathlib import Path
    p = Path(raw)
    if p.is_absolute():
        return str(p)
    # Anchor relative paths to the backend/ root
    backend_dir = Path(__file__).resolve().parent.parent.parent
    resolved = (backend_dir / raw.lstrip("./")).resolve()
    return str(resolved)


def init_firestore():
    """Initialize Firebase Admin SDK once at startup."""
    global _db, _bucket
    if not firebase_admin._apps:
        sa_path = _resolve_sa_path(settings.firebase_service_account_path)
        cred = credentials.Certificate(sa_path)
        firebase_admin.initialize_app(cred, {
            "storageBucket": settings.firebase_storage_bucket
        })
    _db = firestore.client()

    # Storage is optional — requires Blaze plan.
    # Falls back to local disk if not available (see utils/storage.py).
    try:
        _bucket = storage.bucket()
        if not _bucket.name:
            raise ValueError("Empty bucket name")
    except Exception as e:
        logger.warning(
            f"Firebase Storage unavailable ({e}). "
            "Resume/cover letter files will be saved to backend/uploads/ instead."
        )
        _bucket = None




def get_db() -> firestore.Client:
    """Return the Firestore client. Raises if not initialized."""
    if _db is None:
        raise RuntimeError("Firestore not initialized. Call init_firestore() first.")
    return _db


def get_bucket():
    """
    Return the Firebase Storage bucket, or None if Storage is unavailable.
    Callers should use utils/storage.py which handles the local fallback.
    """
    return _bucket
