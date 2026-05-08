"""
Jobs API Routes — Full Phase 3 Implementation

POST /jobs/search   → Trigger grounded job discovery + 92% scoring
GET  /jobs          → Return job_pool from Firestore
GET  /jobs/{job_id} → Return a single job record
GET  /jobs/stats    → Summary counts by decision type
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.job import JobSearchRequest, Decision
from app.agents.job_hunter import hunt_jobs
from app.agents.scorer import score_job
from app.db.user_profile import read_profile, write_task_status, read_preferences
from app.db.job_pool import write_job, read_job, list_jobs, list_jobs_by_decision
from app.db.thought_logs import write_thought_log
from app.models.resume import ResumeProfile, Project, Education
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _dict_to_profile(data: dict) -> ResumeProfile:
    """Reconstruct a ResumeProfile from a Firestore dict."""
    return ResumeProfile(
        name=data.get("name", "User"),
        linkedin_url=data.get("linkedin_url"),
        skills=data.get("skills", []),
        seniority=data.get("seniority", "Mid"),
        years_experience=data.get("years_experience"),
        resume_url=data.get("resume_url"),
        projects=[Project(**p) for p in data.get("projects", [])],
        education=[Education(**e) for e in data.get("education", [])],
    )


async def _run_hunt_and_score(
    user_id: str,
    role: Optional[str],
    location: Optional[str],
    remote: bool,
):
    """
    Background task: hunt jobs → score each → write to job_pool.
    Runs in parallel for all discovered listings.
    """
    # ── Load profile ──────────────────────────────────────────
    profile_data = read_profile(user_id)
    if not profile_data:
        logger.error(f"No profile found for user={user_id}. Aborting hunt.")
        return

    profile = _dict_to_profile(profile_data)

    # ── Merge preferences if not overridden ───────────────────
    prefs = read_preferences(user_id) or {}
    role     = role     or prefs.get("role_type")
    location = location or prefs.get("location")
    remote   = remote   or prefs.get("remote_only", False)

    # ── Update task_status ────────────────────────────────────
    write_task_status(user_id, {
        "agent": "Career_Worker",
        "last_action": "Job_Hunt",
        "status": "Running",
        "target": role or "Software Engineer",
    })
    write_thought_log(user_id, f"Starting job hunt for role: {role or 'inferred from profile'}", "Action")

    # ── Hunt ──────────────────────────────────────────────────
    try:
        listings = await hunt_jobs(profile, role, location, remote)
    except Exception as e:
        logger.error(f"Hunt failed: {e}")
        write_task_status(user_id, {"agent": "Career_Worker", "last_action": "Job_Hunt", "status": "Failed"})
        write_thought_log(user_id, f"Job hunt failed: {str(e)[:120]}", "Error")
        return

    if not listings:
        write_thought_log(user_id, "No job listings found. Try adjusting role or location.", "Warning")
        write_task_status(user_id, {"agent": "Career_Worker", "last_action": "Job_Hunt", "status": "Success"})
        return

    write_thought_log(user_id, f"Found {len(listings)} job listings. Starting 92% scoring analysis...", "Thought")

    # ── Score all jobs in parallel ────────────────────────────
    score_tasks = [
        score_job(
            profile=profile,
            job_title=listing.title,
            job_company=listing.company,
            job_url=listing.url,
            jd_text=listing.description_raw,
            ats_type=listing.ats_type,
            job_id=listing.job_id,
        )
        for listing in listings
    ]

    match_results = await asyncio.gather(*score_tasks, return_exceptions=True)

    # ── Write results to Firestore ────────────────────────────
    auto_apply_count   = 0
    manual_count       = 0
    recommendation_count = 0

    for listing, result in zip(listings, match_results):
        if isinstance(result, Exception):
            logger.warning(f"Scoring failed for {listing.title}: {result}")
            write_thought_log(
                user_id,
                f"Could not score: {listing.title} @ {listing.company}",
                "Warning",
                job_id=listing.job_id,
            )
            continue

        write_job(listing, result, user_id)

        # Thought log per decision
        if result.decision == Decision.AUTO_APPLY:
            auto_apply_count += 1
            write_thought_log(
                user_id,
                f"Perfect match ({result.match_score:.1f}%) — {listing.title} @ {listing.company}. "
                f"Queued for auto-apply.",
                "Success",
                job_id=listing.job_id,
            )
        elif result.decision == Decision.MANUAL_REQUIRED:
            manual_count += 1
            write_thought_log(
                user_id,
                f"Perfect match ({result.match_score:.1f}%) — {listing.title} @ {listing.company}. "
                f"Uses {listing.ats_type.value} — manual application required.",
                "Warning",
                job_id=listing.job_id,
            )
        else:
            recommendation_count += 1

    # ── Final summary ─────────────────────────────────────────
    summary = (
        f"Hunt complete: {len(listings)} jobs scored. "
        f"Auto-apply: {auto_apply_count} | Manual: {manual_count} | Recommendations: {recommendation_count}"
    )
    write_thought_log(user_id, summary, "Success")
    write_task_status(user_id, {
        "agent": "Career_Worker",
        "last_action": "Job_Hunt",
        "status": "Success",
        "target": role or "Software Engineer",
    })
    logger.info(summary)


# ── Routes ────────────────────────────────────────────────────

@router.post("/search", summary="Trigger grounded job search + 92% scoring")
async def search_jobs(req: JobSearchRequest, background_tasks: BackgroundTasks):
    """
    Kicks off the job hunt in the background.
    Returns immediately with a confirmation.
    The frontend should listen to Firestore job_pool and thought_logs for real-time updates.
    """
    user_id = settings.user_id

    # Verify profile exists before hunting
    if not read_profile(user_id):
        raise HTTPException(
            status_code=400,
            detail="No resume profile found. Upload and parse your resume first."
        )

    background_tasks.add_task(
        _run_hunt_and_score,
        user_id=user_id,
        role=req.role,
        location=req.location,
        remote=req.remote or False,
    )

    location_str = "remote" if req.remote else f"in {req.location or 'any location'}"
    return {
        "status": "hunting",
        "message": (
            f"Job hunt started for '{req.role or 'inferred role'}' {location_str}. "
            "Watch Zone B and Zone C for live updates."
        ),
        "user_id": user_id,
    }


@router.get("/", summary="Get all jobs in the job pool")
async def get_jobs(
    decision: Optional[str] = Query(None, description="Filter by: AUTO_APPLY, MANUAL_REQUIRED, RECOMMENDATION"),
    limit: int = Query(50, le=100),
):
    """Return job_pool from Firestore, optionally filtered by decision."""
    user_id = settings.user_id

    if decision:
        try:
            decision_enum = Decision(decision.upper())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid decision filter. Use: AUTO_APPLY, MANUAL_REQUIRED, RECOMMENDATION"
            )
        jobs = list_jobs_by_decision(user_id, decision_enum)
    else:
        jobs = list_jobs(user_id, limit=limit)

    return {
        "total": len(jobs),
        "jobs": jobs,
        "user_id": user_id,
    }


@router.get("/stats", summary="Job pool summary counts")
async def get_job_stats():
    """Return counts of jobs per decision type."""
    user_id = settings.user_id
    auto   = list_jobs_by_decision(user_id, Decision.AUTO_APPLY)
    manual = list_jobs_by_decision(user_id, Decision.MANUAL_REQUIRED)
    recs   = list_jobs_by_decision(user_id, Decision.RECOMMENDATION)
    return {
        "auto_apply":      len(auto),
        "manual_required": len(manual),
        "recommendations": len(recs),
        "total":           len(auto) + len(manual) + len(recs),
    }


@router.get("/{job_id}", summary="Get a single job by ID")
async def get_job(job_id: str):
    """Return a single job record from job_pool."""
    job = read_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return job
