"""
Applications API Routes — Phase 5

POST /applications/run   → Trigger parallel auto-apply missions
GET  /applications/      → List all application records
GET  /applications/{id}  → Get single application detail
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from app.config import settings
from app.db.applications import list_applications, read_application
from app.db.job_pool import list_jobs_by_decision
from app.db.user_profile import read_profile
from app.models.job import Decision
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class RunMissionsRequest(BaseModel):
    max_concurrent: int = 3
    cover_letter: Optional[str] = None


async def _fetch_resume_bytes(user_id: str) -> Optional[bytes]:
    """Download resume PDF bytes from Firebase Storage URL in the profile."""
    import httpx
    try:
        profile = read_profile(user_id)
        resume_url = profile.get("resume_url") if profile else None
        if not resume_url:
            return None
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(resume_url)
            if resp.status_code == 200:
                return resp.content
    except Exception as e:
        logger.warning(f"Could not fetch resume bytes: {e}")
    return None


async def _run_missions_bg(user_id: str, max_concurrent: int, cover_letter: Optional[str]):
    """Background task: fetch AUTO_APPLY jobs → run parallel missions."""
    from app.agents.auto_apply import run_parallel_missions

    auto_jobs = list_jobs_by_decision(user_id, Decision.AUTO_APPLY)
    if not auto_jobs:
        logger.info(f"No AUTO_APPLY jobs in pool for user={user_id}")
        return

    resume_bytes = await _fetch_resume_bytes(user_id)
    if not resume_bytes:
        logger.warning("Resume bytes unavailable — proceeding without file upload.")

    await run_parallel_missions(
        jobs=auto_jobs,
        user_id=user_id,
        resume_bytes=resume_bytes,
        cover_letter=cover_letter,
        max_concurrent=max_concurrent,
    )


@router.post("/run", summary="Launch parallel auto-apply missions for all AUTO_APPLY jobs")
async def run_missions(req: RunMissionsRequest, background_tasks: BackgroundTasks):
    """
    Kicks off parallel Playwright missions in the background.
    Only targets jobs with decision = AUTO_APPLY (Lever + Greenhouse).
    Returns immediately; check /applications/ for live status updates.
    """
    user_id = settings.user_id

    if not read_profile(user_id):
        raise HTTPException(status_code=400, detail="No profile found. Upload resume first.")

    auto_jobs = list_jobs_by_decision(user_id, Decision.AUTO_APPLY)
    if not auto_jobs:
        raise HTTPException(
            status_code=404,
            detail=(
                "No AUTO_APPLY jobs found in the pool. "
                "Run a job search first (POST /jobs/search)."
            )
        )

    background_tasks.add_task(
        _run_missions_bg,
        user_id=user_id,
        max_concurrent=min(req.max_concurrent, 5),  # cap at 5
        cover_letter=req.cover_letter,
    )

    return {
        "status": "running",
        "jobs_queued": len(auto_jobs),
        "max_concurrent": min(req.max_concurrent, 5),
        "message": (
            f"Launching {len(auto_jobs)} auto-apply missions with concurrency={min(req.max_concurrent,5)}. "
            "Watch Zone B for real-time status."
        ),
    }


@router.get("/", summary="List all application records")
async def list_apps():
    """Return all application records for the user, newest first."""
    user_id = settings.user_id
    apps = list_applications(user_id)
    return {
        "total":        len(apps),
        "submitted":    sum(1 for a in apps if a.get("status") == "submitted"),
        "captcha":      sum(1 for a in apps if a.get("status") == "manual_intervention_required"),
        "failed":       sum(1 for a in apps if a.get("status") == "failed"),
        "applications": apps,
    }


@router.get("/{app_id}", summary="Get a single application record")
async def get_application(app_id: str):
    """Return details for a single application by ID."""
    app = read_application(app_id)
    if not app:
        raise HTTPException(status_code=404, detail=f"Application '{app_id}' not found.")
    return app
