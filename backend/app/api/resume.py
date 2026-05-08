"""
Resume API Routes — Full Phase 2 Implementation
POST /resume/upload  → Store PDF in Firebase Storage
POST /resume/parse   → Gemini extraction → Firestore profile write
GET  /resume/profile → Read current profile
POST /resume/preferences → Save job search preferences
"""
import io
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from fastapi.responses import JSONResponse

from app.config import settings
from app.utils.pdf_reader import extract_text_from_bytes
from app.utils.storage import upload_resume
from app.utils import storage as storage_utils
from app.agents.resume_parser import parse_resume, generate_audit_message
from app.db.user_profile import (
    write_profile,
    read_profile,
    update_resume_url,
    write_preferences,
    read_preferences,
    write_task_status,
)
from app.models.resume import ParseResumeResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# In-memory store for the raw PDF bytes during the session
# (keyed by user_id — single user, so simple dict is fine)
_pdf_cache: dict[str, bytes] = {}
_filename_cache: dict[str, str] = {}


@router.post("/upload", summary="Upload a resume PDF to Firebase Storage")
async def upload_resume_endpoint(file: UploadFile = File(...)):
    """
    Step 1 of ingestion: accept the PDF, store it in Firebase Storage,
    cache raw bytes for parsing, and return the storage URL.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    pdf_bytes = await file.read()
    if len(pdf_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File size exceeds 10 MB limit.")

    user_id = settings.user_id

    # ── Upload to Firebase Storage ────────────────────────────
    try:
        resume_url = upload_resume(user_id, pdf_bytes, file.filename)
    except Exception as e:
        logger.error(f"Storage upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {str(e)}")

    # ── Cache bytes for parse step ────────────────────────────
    _pdf_cache[user_id] = pdf_bytes
    _filename_cache[user_id] = file.filename

    # ── Update resume_url in Firestore if profile exists ─────
    try:
        update_resume_url(user_id, resume_url)
    except Exception:
        pass  # profile may not exist yet — parse step creates it

    logger.info(f"Resume uploaded: filename={file.filename} user={user_id}")

    return {
        "status": "uploaded",
        "user_id": user_id,
        "filename": file.filename,
        "resume_url": resume_url,
        "message": "Resume uploaded. Call POST /resume/parse to extract your profile.",
    }


@router.post("/parse", summary="Parse uploaded resume with Gemini 2.0 Flash")
async def parse_resume_endpoint():
    """
    Step 2 of ingestion: extract text from the cached PDF,
    send to Gemini, write structured profile to Firestore,
    and return the profile + Zone A audit message.
    """
    user_id = settings.user_id

    if user_id not in _pdf_cache:
        raise HTTPException(
            status_code=400,
            detail="No resume found for this session. Upload a PDF first via POST /resume/upload."
        )

    pdf_bytes = _pdf_cache[user_id]

    # ── Extract Text ──────────────────────────────────────────
    try:
        raw_text = extract_text_from_bytes(pdf_bytes)
    except Exception as e:
        logger.error(f"PDF text extraction failed: {e}")
        raise HTTPException(status_code=422, detail=f"Could not read PDF: {str(e)}")

    if len(raw_text.strip()) < 100:
        raise HTTPException(
            status_code=422,
            detail="Extracted text is too short. The PDF may be scanned/image-based."
        )

    # ── Update task_status ────────────────────────────────────
    write_task_status(user_id, {
        "agent": "Career_Worker",
        "last_action": "Resume_Parse",
        "status": "Running",
        "target": None,
        "score": None,
    })

    # ── Gemini Extraction ─────────────────────────────────────
    try:
        profile = await parse_resume(raw_text)
    except Exception as e:
        # Unwrap tenacity RetryError to get the real underlying exception
        real_exc = getattr(e, "last_attempt", None)
        if real_exc:
            try:
                real_exc = real_exc.result()
            except Exception as inner:
                real_exc = inner
        detail = str(real_exc or e)
        write_task_status(user_id, {
            "agent": "Career_Worker",
            "last_action": "Resume_Parse",
            "status": "Failed",
        })
        logger.error(f"Gemini parse failed: {detail}")
        raise HTTPException(status_code=500, detail=f"Gemini parsing failed: {detail}")

    # ── Attach resume_url from storage ────────────────────────
    existing = read_profile(user_id)
    if existing and existing.get("resume_url"):
        profile.resume_url = existing["resume_url"]

    # ── Write to Firestore ────────────────────────────────────
    write_profile(user_id, profile)

    # ── Generate Zone A Audit Message ─────────────────────────
    try:
        audit_message = await generate_audit_message(profile)
    except Exception as e:
        logger.warning(f"Audit message generation failed (non-fatal): {e}")
        top_skills = ", ".join(profile.skills[:2]) if profile.skills else "your core skills"
        audit_message = (
            f"I've mapped your profile. You are strongest in {top_skills}. "
            f"Should I prioritize a specific location or focus on role type regardless of geography?"
        )

    # ── Update task_status to success ─────────────────────────
    write_task_status(user_id, {
        "agent": "Career_Worker",
        "last_action": "Resume_Parse",
        "status": "Success",
        "target": None,
        "score": None,
    })

    # ── Write audit message to thought_logs ───────────────────
    try:
        from app.db.firestore_client import get_db
        import uuid
        db = get_db()
        db.collection("thought_logs").document(str(uuid.uuid4())).set({
            "userId": user_id,
            "type": "Success",
            "message": f"Resume analysis complete. Extracted {len(profile.skills)} skills. Seniority: {profile.seniority}.",
            "timestamp": datetime.now(timezone.utc),
        })
    except Exception:
        pass

    # ── Auto-match jobs from master_jobs pool ─────────────────
    try:
        from app.agents.job_matcher import match_jobs_for_user
        db2 = get_db() if 'db' not in dir() else get_db()
        import uuid as _uuid

        # Log: starting match
        db2.collection("thought_logs").document(str(_uuid.uuid4())).set({
            "userId": user_id,
            "type": "Thought",
            "message": f"Scanning job database for matches based on your {len(profile.skills)} skills...",
            "timestamp": datetime.now(timezone.utc),
        })

        matched_count = match_jobs_for_user(user_id, profile)

        # Log: result
        db2.collection("thought_logs").document(str(_uuid.uuid4())).set({
            "userId": user_id,
            "type": "Success" if matched_count > 0 else "Action",
            "message": (
                f"Job matching complete: {matched_count} positions found above threshold. "
                f"Zone C updated — check the Job Vault."
            ) if matched_count > 0 else
            "No jobs matched your profile above the threshold. Try expanding your skillset.",
            "timestamp": datetime.now(timezone.utc),
        })

        logger.info(f"Job matching triggered after resume parse: {matched_count} jobs written.")
    except Exception as e:
        logger.warning(f"Job matching failed (non-fatal): {e}")

    return ParseResumeResponse(
        user_id=user_id,
        profile=profile,
        audit_message=audit_message,
    )



@router.get("/profile", summary="Get the current parsed user profile")
async def get_profile():
    """Return the user's Firestore profile."""
    user_id = settings.user_id
    profile = read_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Upload and parse a resume first.")
    return {"user_id": user_id, "profile": profile}


@router.post("/preferences", summary="Save job search preferences")
async def save_preferences(preferences: dict = Body(...)):
    """
    Save location, role_type, remote preference after Zone A audit dialogue.
    Example body: {"location": "Bangalore", "role_type": "AIML Engineer", "remote": false}
    """
    user_id = settings.user_id
    write_preferences(user_id, preferences)
    return {
        "status": "saved",
        "user_id": user_id,
        "preferences": preferences,
        "message": "Preferences saved. Ready to start the job hunt.",
    }
