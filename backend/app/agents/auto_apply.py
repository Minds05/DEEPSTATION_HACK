"""
Auto-Apply Mission Executor — Phase 5 Core

Executes a single autonomous browser mission for one job listing:
  1. Open isolated browser context
  2. Navigate to application URL
  3. Detect CAPTCHA → pause if found
  4. Map DOM fields to profile data
  5. Fill all visible fields
  6. Upload resume PDF
  7. Click submit
  8. Detect confirmation page
  9. Screenshot + write to Firestore applications collection
 10. Emit thought logs throughout

The orchestrator calls run_parallel_missions() which wraps this
with asyncio.gather() for concurrent execution.
"""
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.config import settings
from app.models.application import ApplicationRecord, AppStatus
from app.db.applications import create_application, update_application_status
from app.db.user_profile import read_profile, write_task_status
from app.db.thought_logs import write_thought_log
from app.utils.storage import upload_screenshot
from app.utils.screenshot import capture_confirmation, capture_screenshot
from app.browser.browser_controller import new_browser_context, navigate
from app.browser.dom_mapper import build_fill_plan, find_resume_upload_input, find_submit_button
from app.browser.form_filler import fill_fields, upload_resume, click_submit, is_confirmation_page
from app.browser.captcha_guard import detect_captcha, handle_captcha
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def run_single_mission(
    job_id: str,
    job_url: str,
    job_title: str,
    job_company: str,
    match_score: float,
    ats_type: str,
    user_id: str,
    resume_bytes: Optional[bytes] = None,
    cover_letter: Optional[str] = None,
) -> ApplicationRecord:
    """
    Execute a complete auto-apply mission for one job.
    Returns the final ApplicationRecord with status.
    """
    app_id = str(uuid.uuid4())
    record = ApplicationRecord(
        app_id=app_id,
        job_id=job_id,
        user_id=user_id,
        status=AppStatus.RUNNING,
        match_score=match_score,
        ats_type=ats_type,
        timestamp=datetime.now(timezone.utc),
    )

    # Write initial record
    create_application(record)

    write_thought_log(
        user_id, f"Starting auto-apply: {job_title} @ {job_company}",
        "Action", job_id=job_id, app_id=app_id,
    )

    try:
        async with new_browser_context() as (context, page):

            # ── 1. Navigate ───────────────────────────────────
            ok = await navigate(page, job_url)
            if not ok:
                raise RuntimeError(f"Could not navigate to: {job_url}")

            await asyncio.sleep(2)   # let JS render

            # ── 2. CAPTCHA check ──────────────────────────────
            if await detect_captcha(page):
                result = await handle_captcha(page, job_id, app_id, user_id)
                screenshot_bytes = result.get("screenshot_bytes", b"")
                screenshot_url = None
                if screenshot_bytes:
                    screenshot_url = upload_screenshot(user_id, app_id, screenshot_bytes)

                update_application_status(
                    app_id, AppStatus.CAPTCHA,
                    screenshot_url=screenshot_url,
                    error_log="CAPTCHA detected — manual intervention required.",
                )
                record.status = AppStatus.CAPTCHA
                record.screenshot_url = screenshot_url
                return record

            # ── 3. Load profile ───────────────────────────────
            profile = read_profile(user_id) or {}

            # ── 4. Map DOM fields ─────────────────────────────
            fill_plan = await build_fill_plan(page, profile, cover_letter)

            if not fill_plan:
                write_thought_log(
                    user_id,
                    f"⚠️ No fillable fields found on {job_company} page. Skipping.",
                    "Warning", job_id=job_id, app_id=app_id,
                )
                update_application_status(app_id, AppStatus.SKIPPED, error_log="No fillable fields.")
                record.status = AppStatus.SKIPPED
                return record

            write_thought_log(
                user_id,
                f"Mapped {len(fill_plan)} fields on {job_company} application form.",
                "Thought", job_id=job_id, app_id=app_id,
            )

            # ── 5. Fill fields ────────────────────────────────
            filled = await fill_fields(page, fill_plan)
            write_thought_log(
                user_id, f"Filled {filled} fields on form.",
                "Action", job_id=job_id, app_id=app_id,
            )

            # ── 6. Upload resume ──────────────────────────────
            if resume_bytes:
                upload_selector = await find_resume_upload_input(page)
                if upload_selector:
                    uploaded = await upload_resume(page, upload_selector, resume_bytes)
                    if uploaded:
                        write_thought_log(
                            user_id, "Resume PDF uploaded to form.",
                            "Action", job_id=job_id, app_id=app_id,
                        )

            # ── 7. Submit ─────────────────────────────────────
            submit_selector = await find_submit_button(page)
            if not submit_selector:
                raise RuntimeError("Submit button not found — cannot complete application.")

            submitted = await click_submit(page, submit_selector)

            # ── 8. Confirm ────────────────────────────────────
            confirmed = await is_confirmation_page(page)

            # ── 9. Screenshot ─────────────────────────────────
            screen_bytes = await capture_confirmation(page)
            screenshot_url = None
            if screen_bytes:
                screenshot_url = upload_screenshot(user_id, app_id, screen_bytes)

            # ── 10. Update record ─────────────────────────────
            final_status = AppStatus.SUBMITTED if (submitted or confirmed) else AppStatus.FAILED
            update_application_status(
                app_id, final_status, screenshot_url=screenshot_url
            )
            record.status = final_status
            record.screenshot_url = screenshot_url

            if final_status == AppStatus.SUBMITTED:
                write_thought_log(
                    user_id,
                    f"✅ Applied to {job_title} @ {job_company} — confirmation captured.",
                    "Success", job_id=job_id, app_id=app_id,
                )
            else:
                write_thought_log(
                    user_id,
                    f"⚠️ Could not confirm submission for {job_title} @ {job_company}.",
                    "Warning", job_id=job_id, app_id=app_id,
                )

    except Exception as e:
        error_msg = str(e)[:400]
        logger.error(f"Mission failed for job_id={job_id}: {error_msg}")
        update_application_status(app_id, AppStatus.FAILED, error_log=error_msg)
        write_thought_log(
            user_id,
            f"❌ Mission failed: {job_title} @ {job_company}. Error: {error_msg}",
            "Error", job_id=job_id, app_id=app_id,
        )
        record.status = AppStatus.FAILED
        record.error_log = error_msg

    return record


async def run_parallel_missions(
    jobs: list[dict],
    user_id: str,
    resume_bytes: Optional[bytes] = None,
    cover_letter: Optional[str] = None,
    max_concurrent: int = 3,
) -> list[ApplicationRecord]:
    """
    Execute multiple auto-apply missions in parallel.
    Caps concurrency at max_concurrent (default: 3) to avoid detection.

    Args:
        jobs:           List of job dicts from job_pool (AUTO_APPLY decision only)
        user_id:        Firestore user ID
        resume_bytes:   Raw PDF bytes to upload to each form
        cover_letter:   Optional cover letter text
        max_concurrent: Max simultaneous browser sessions

    Returns:
        List of ApplicationRecord objects with final statuses.
    """
    if not jobs:
        return []

    semaphore = asyncio.Semaphore(max_concurrent)

    write_task_status(user_id, {
        "agent": "Career_Worker",
        "last_action": "Auto_Apply",
        "status": "Running",
        "target": f"{len(jobs)} jobs",
    })

    write_thought_log(
        user_id,
        f"Launching parallel auto-apply missions for {len(jobs)} jobs "
        f"(concurrency: {max_concurrent}).",
        "Action",
    )

    async def _bounded_mission(job: dict) -> ApplicationRecord:
        async with semaphore:
            return await run_single_mission(
                job_id=job["jobId"],
                job_url=job["url"],
                job_title=job.get("title", "Unknown Role"),
                job_company=job.get("company", "Unknown Company"),
                match_score=job.get("matchScore", 0.0),
                ats_type=job.get("atsType", "unknown"),
                user_id=user_id,
                resume_bytes=resume_bytes,
                cover_letter=cover_letter,
            )

    tasks = [_bounded_mission(job) for job in jobs]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter exceptions into failed records
    records = []
    for job, result in zip(jobs, results):
        if isinstance(result, Exception):
            logger.error(f"Unhandled exception for job {job['jobId']}: {result}")
            records.append(ApplicationRecord(
                job_id=job["jobId"],
                user_id=user_id,
                status=AppStatus.FAILED,
                error_log=str(result)[:400],
            ))
        else:
            records.append(result)

    submitted = sum(1 for r in records if r.status == AppStatus.SUBMITTED)
    captcha   = sum(1 for r in records if r.status == AppStatus.CAPTCHA)
    failed    = sum(1 for r in records if r.status == AppStatus.FAILED)

    write_thought_log(
        user_id,
        f"Parallel missions complete: {submitted} submitted | "
        f"{captcha} captcha-blocked | {failed} failed.",
        "Success",
    )

    write_task_status(user_id, {
        "agent": "Career_Worker",
        "last_action": "Auto_Apply",
        "status": "Success",
    })

    return records
