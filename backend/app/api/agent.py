"""
Agent API Routes — Phase 6/7

POST /agent/cover-letter    → Generate + upload cover letter for a MANUAL_REQUIRED job
POST /agent/start           → Full orchestrator start (Phase 7)
GET  /agent/stream          → SSE thought log stream (Phase 7)
GET  /agent/status          → Current task_status
"""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from app.config import settings
from app.db.user_profile import read_profile, read_preferences
from app.db.job_pool import read_job, list_jobs_by_decision
from app.db.thought_logs import write_thought_log, get_recent_logs
from app.db.firestore_client import get_db
from app.models.job import Decision
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class CoverLetterRequest(BaseModel):
    job_id: str


# ── Cover Letter ──────────────────────────────────────────────

@router.post("/cover-letter", summary="Generate a cover letter for a MANUAL_REQUIRED job")
async def generate_cover_letter_endpoint(req: CoverLetterRequest):
    """
    Generates a Gemini 2.0 Flash cover letter for a specific job,
    exports it as a PDF, uploads to Firebase Storage, and returns the URL.
    """
    from app.agents.cover_letter import generate_cover_letter, generate_pdf
    from app.utils.storage import upload_cover_letter
    from app.models.resume import ResumeProfile, Project, Education

    user_id = settings.user_id

    # ── Load profile ──────────────────────────────────────────
    profile_data = read_profile(user_id)
    if not profile_data:
        raise HTTPException(status_code=400, detail="No profile found. Upload resume first.")

    profile = ResumeProfile(
        name=profile_data.get("name", "Candidate"),
        skills=profile_data.get("skills", []),
        seniority=profile_data.get("seniority", "Mid"),
        years_experience=profile_data.get("years_experience"),
        linkedin_url=profile_data.get("linkedin_url"),
        projects=[Project(**p) for p in profile_data.get("projects", [])],
        education=[Education(**e) for e in profile_data.get("education", [])],
    )

    # ── Load job ──────────────────────────────────────────────
    job = read_job(req.job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{req.job_id}' not found.")

    write_thought_log(
        user_id,
        f"Generating cover letter for {job.get('title')} @ {job.get('company')}...",
        "Action",
        job_id=req.job_id,
    )

    # ── Generate text ─────────────────────────────────────────
    try:
        letter_text = await generate_cover_letter(
            profile=profile,
            job_title=job.get("title", ""),
            job_company=job.get("company", ""),
            jd_text=job.get("descriptionRaw", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cover letter generation failed: {e}")

    # ── Export PDF ────────────────────────────────────────────
    pdf_bytes = generate_pdf(
        cover_letter_text=letter_text,
        candidate_name=profile.name,
        job_title=job.get("title", ""),
        company=job.get("company", ""),
    )

    # ── Upload to Storage ─────────────────────────────────────
    try:
        cover_letter_url = upload_cover_letter(user_id, req.job_id, pdf_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {e}")

    # ── Write to job_pool record ──────────────────────────────
    try:
        get_db().collection("job_pool").document(req.job_id).update({
            "coverLetterUrl": cover_letter_url,
            "coverLetterText": letter_text,   # cached for display
            "updatedAt": datetime.now(timezone.utc),
        })
    except Exception as e:
        logger.warning(f"Could not update job_pool with cover letter URL: {e}")

    write_thought_log(
        user_id,
        f"Cover letter ready for {job.get('title')} @ {job.get('company')}. Download: {cover_letter_url}",
        "Success", job_id=req.job_id,
    )

    return {
        "status": "ready",
        "job_id": req.job_id,
        "cover_letter_url": cover_letter_url,
        "cover_letter_text": letter_text,
        "word_count": len(letter_text.split()),
        "message": f"Cover letter generated and uploaded. Open the job page manually and upload it.",
    }

class ChatRequest(BaseModel):
    message: str

@router.post("/chat", summary="Process natural language preferences via chat")
async def chat_preferences_endpoint(req: ChatRequest, background_tasks: BackgroundTasks):
    import json
    import google.generativeai as genai
    from app.db.user_profile import write_preferences
    from app.db.thought_logs import write_thought_log
    from app.agents.job_matcher import match_jobs_for_user
    from app.models.resume import ResumeProfile

    user_id = settings.user_id
    
    write_thought_log(user_id, f"User said: {req.message}", "Thought")
    
    # Use Gemini to extract JSON preferences
    model = genai.GenerativeModel(
        model_name=settings.gemini_model,
        generation_config={"response_mime_type": "application/json"}
    )
    
    prompt = f"""
    The user is chatting with a career agent. Extract any job preferences from this message:
    "{req.message}"
    
    Return a JSON object with these exact keys. Use null if not mentioned.
    {{
        "company": "specific company name, e.g. AWS, Google",
        "location": "location name e.g. New York, Remote",
        "role": "job title e.g. Software Engineer"
    }}
    """
    
    try:
        r = await model.generate_content_async(prompt)
        extracted = json.loads(r.text)
        
        # Clean nulls
        extracted = {k: v for k, v in extracted.items() if v is not None}
        
        if extracted:
            write_preferences(user_id, extracted)
            write_thought_log(user_id, f"Extracted preferences: {extracted}", "Action")
            
            # Trigger rematch in background
            profile_data = read_profile(user_id)
            if profile_data:
                profile = ResumeProfile(**profile_data)
                background_tasks.add_task(match_jobs_for_user, user_id=user_id, profile=profile)
                write_thought_log(user_id, "Re-running job matcher with new preferences...", "Thought")
            
            # Build a natural response
            prefs_text = []
            if "company" in extracted:
                prefs_text.append(f"at {extracted['company']}")
            if "role" in extracted:
                prefs_text.append(f"for {extracted['role']} roles")
            if "location" in extracted:
                prefs_text.append(f"in {extracted['location']}")
            
            summary = " ".join(prefs_text) if prefs_text else "your new preferences"
            
            return {"reply": f"Got it! I've updated my search to look for jobs {summary}. I'm re-matching your Job Vault right now!"}
        else:
            return {"reply": "I couldn't identify any specific job preferences from your message."}
            
    except Exception as e:
        logger.error(f"Chat extraction failed: {e}")
        return {"reply": "Sorry, I had trouble processing that request."}
# ── Agent Status ──────────────────────────────────────────────

@router.get("/status", summary="Current orchestrator task status")
async def get_agent_status():
    """Return the current task_status from Firestore."""
    user_id = settings.user_id
    db = get_db()
    doc = db.collection("users").document(user_id)\
             .collection("task_status").document("current").get()
    status = doc.to_dict() if doc.exists else {"status": "Idle", "agent": "Career_Worker"}
    return status


# ── SSE Stream ────────────────────────────────────────────────

@router.get("/stream", summary="SSE stream of live thought logs (Phase 7)")
async def stream_thought_logs():
    """
    Server-Sent Events endpoint.
    Streams the last 50 thought logs from Firestore on connection,
    then holds open. Full real-time streaming is wired in Phase 7.
    """
    import json

    user_id = settings.user_id
    logs = get_recent_logs(user_id, limit=50)

    async def event_generator():
        for log in reversed(logs):
            # Convert Firestore timestamp to ISO string
            ts = log.get("timestamp")
            if hasattr(ts, "isoformat"):
                log["timestamp"] = ts.isoformat()
            elif hasattr(ts, "strftime"):
                log["timestamp"] = ts.strftime("%Y-%m-%dT%H:%M:%S")

            yield f"data: {json.dumps(log)}\n\n"

        # Keep connection alive
        while True:
            import asyncio
            await asyncio.sleep(30)
            yield ": keepalive\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── Orchestrator Start ────────────────────────────────────────

class StartRequest(BaseModel):
    role:       Optional[str] = None
    location:   Optional[str] = None
    remote:     bool          = False
    skip_hunt:  bool          = False
    skip_apply: bool          = False


@router.post("/start", summary="Launch the full C-IAW orchestrator loop")
async def start_orchestrator(req: StartRequest, background_tasks: BackgroundTasks):
    """
    Kicks off the end-to-end pipeline in the background:
    Hunt → Score → Auto-Apply → Cover Letters
    Returns immediately; watch Zone B for live progress.
    """
    from app.agents.orchestrator import run_orchestrator

    user_id = settings.user_id

    if not read_profile(user_id):
        raise HTTPException(
            status_code=400,
            detail="No profile found. Upload and parse your resume first."
        )

    background_tasks.add_task(
        run_orchestrator,
        user_id=user_id,
        role=req.role,
        location=req.location,
        remote=req.remote,
        skip_hunt=req.skip_hunt,
        skip_apply=req.skip_apply,
    )

    return {
        "status": "started",
        "message": (
            "Full C-IAW orchestrator launched. "
            "Watch Zone B for live thought logs and Zone C for job updates."
        ),
        "config": req.model_dump(),
    }
