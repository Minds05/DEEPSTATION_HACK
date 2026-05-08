"""
Orchestrator — Full End-to-End C-IAW Loop (Phase 7)

Executes the complete career agent workflow:
  Step 1: Ingest profile (already done by Phase 2 resume parse)
  Step 2: Hunt jobs (Phase 3 search grounding)
  Step 3: Score all jobs (Phase 3 scorer)
  Step 4: Run auto-apply missions in parallel (Phase 5)
  Step 5: Generate cover letters for MANUAL_REQUIRED jobs (Phase 6)
  Step 6: Emit final summary to Zone A + Zone B

Called by POST /agent/start
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional

from app.config import settings
from app.db.user_profile import read_profile, read_preferences, write_task_status
from app.db.job_pool import list_jobs_by_decision, list_jobs
from app.db.thought_logs import write_thought_log
from app.models.job import Decision
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def run_orchestrator(
    user_id: str,
    role: Optional[str] = None,
    location: Optional[str] = None,
    remote: bool = False,
    skip_hunt: bool = False,
    skip_apply: bool = False,
) -> dict:
    """
    Full C-IAW orchestration loop.

    Args:
        user_id:     Firestore user ID
        role:        Target role (overrides preferences)
        location:    Target location (overrides preferences)
        remote:      Remote-only flag
        skip_hunt:   Skip job hunt (use existing job_pool)
        skip_apply:  Hunt + score only, do not apply

    Returns:
        Summary dict with counts of outcomes.
    """
    write_task_status(user_id, {
        "agent": "Career_Worker",
        "last_action": "Orchestrator_Start",
        "status": "Running",
        "target": role or "auto",
    })
    write_thought_log(user_id, "🚀 C-IAW Orchestrator started. Full loop initiated.", "Action")

    summary = {
        "jobs_discovered": 0,
        "jobs_above_threshold": 0,
        "auto_apply_submitted": 0,
        "manual_required": 0,
        "recommendations": 0,
        "cover_letters_generated": 0,
        "errors": 0,
    }

    # ── Step 1: Load profile ──────────────────────────────────
    profile_data = read_profile(user_id)
    if not profile_data:
        write_thought_log(user_id, "❌ No profile found. Upload resume first.", "Error")
        write_task_status(user_id, {"agent": "Career_Worker", "status": "Failed"})
        return {"error": "no_profile"}

    prefs = read_preferences(user_id) or {}
    role     = role     or prefs.get("role_type")
    location = location or prefs.get("location")
    remote   = remote   or prefs.get("remote_only", False)

    # ── Step 2: Hunt + Score ──────────────────────────────────
    if not skip_hunt:
        from app.api.jobs import _run_hunt_and_score
        write_thought_log(user_id, f"Starting job hunt: role={role or 'inferred'} location={location or 'any'}", "Action")
        await _run_hunt_and_score(user_id, role, location, remote)

    # ── Tally job pool ────────────────────────────────────────
    all_jobs  = list_jobs(user_id)
    auto_jobs = list_jobs_by_decision(user_id, Decision.AUTO_APPLY)
    manual    = list_jobs_by_decision(user_id, Decision.MANUAL_REQUIRED)
    recs      = list_jobs_by_decision(user_id, Decision.RECOMMENDATION)

    summary["jobs_discovered"]      = len(all_jobs)
    summary["jobs_above_threshold"] = len(auto_jobs) + len(manual)
    summary["manual_required"]      = len(manual)
    summary["recommendations"]      = len(recs)

    write_thought_log(
        user_id,
        f"Job pool: {len(all_jobs)} total | {len(auto_jobs)} auto | "
        f"{len(manual)} manual | {len(recs)} recommendations.",
        "Thought",
    )

    # ── Step 3: Auto-Apply ────────────────────────────────────
    if not skip_apply and auto_jobs:
        from app.agents.auto_apply import run_parallel_missions
        import httpx

        # Fetch resume bytes for upload
        resume_bytes = None
        resume_url = profile_data.get("resume_url")
        if resume_url:
            try:
                async with httpx.AsyncClient(timeout=20) as client:
                    resp = await client.get(resume_url)
                    if resp.status_code == 200:
                        resume_bytes = resp.content
            except Exception as e:
                logger.warning(f"Resume download failed: {e}")

        write_thought_log(user_id, f"Launching {len(auto_jobs)} auto-apply missions...", "Action")
        records = await run_parallel_missions(
            jobs=auto_jobs,
            user_id=user_id,
            resume_bytes=resume_bytes,
            max_concurrent=3,
        )

        from app.models.application import AppStatus
        submitted = sum(1 for r in records if r.status == AppStatus.SUBMITTED)
        summary["auto_apply_submitted"] = submitted
        summary["errors"] += sum(1 for r in records if r.status == AppStatus.FAILED)

    # ── Step 4: Cover letters for MANUAL_REQUIRED ─────────────
    if manual:
        from app.agents.cover_letter import generate_cover_letter, generate_pdf
        from app.utils.storage import upload_cover_letter
        from app.models.resume import ResumeProfile, Project, Education
        from app.db.firestore_client import get_db

        profile = ResumeProfile(
            name=profile_data.get("name", "Candidate"),
            skills=profile_data.get("skills", []),
            seniority=profile_data.get("seniority", "Mid"),
            years_experience=profile_data.get("years_experience"),
            projects=[Project(**p) for p in profile_data.get("projects", [])],
            education=[Education(**e) for e in profile_data.get("education", [])],
        )

        write_thought_log(user_id, f"Generating cover letters for {len(manual)} manual jobs...", "Action")

        async def _gen_cover(job: dict):
            try:
                text = await generate_cover_letter(
                    profile=profile,
                    job_title=job.get("title", ""),
                    job_company=job.get("company", ""),
                    jd_text=job.get("descriptionRaw", ""),
                )
                pdf_bytes = generate_pdf(text, profile.name, job.get("title", ""), job.get("company", ""))
                url = upload_cover_letter(user_id, job["jobId"], pdf_bytes)
                get_db().collection("job_pool").document(job["jobId"]).update({
                    "coverLetterUrl": url,
                    "coverLetterText": text,
                    "updatedAt": datetime.now(timezone.utc),
                })
                write_thought_log(
                    user_id,
                    f"Cover letter ready: {job.get('title')} @ {job.get('company')}",
                    "Success", job_id=job["jobId"],
                )
                return True
            except Exception as e:
                logger.error(f"Cover letter failed for {job.get('title')}: {e}")
                return False

        results = await asyncio.gather(*[_gen_cover(j) for j in manual[:10]])
        summary["cover_letters_generated"] = sum(results)

    # ── Final summary ─────────────────────────────────────────
    summary_msg = (
        f"🏁 Orchestrator complete. "
        f"{summary['auto_apply_submitted']}/{len(auto_jobs)} auto-applied | "
        f"{summary['cover_letters_generated']}/{len(manual)} cover letters ready | "
        f"{summary['recommendations']} recommendations."
    )
    write_thought_log(user_id, summary_msg, "Success")
    write_task_status(user_id, {
        "agent": "Career_Worker",
        "last_action": "Orchestrator_Complete",
        "status": "Success",
        "target": None,
    })

    logger.info(summary_msg)
    return summary
