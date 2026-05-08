"""
Form Filler — Fills discovered form fields with profile data.
Uses Playwright to type into inputs, fill textareas, and upload files.
"""
import asyncio
import tempfile
import os
from typing import Optional

from playwright.async_api import Page
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Typing speed simulation (ms between keystrokes)
_TYPE_DELAY = 30


async def fill_fields(page: Page, fill_plan: dict[str, str]) -> int:
    """
    Execute the fill plan: type values into each mapped field.
    Returns the number of fields successfully filled.
    """
    filled = 0
    for selector, value in fill_plan.items():
        if not value:
            continue
        try:
            el = await page.query_selector(selector)
            if not el:
                continue
            if not await el.is_visible():
                continue

            # Clear existing value first
            await el.triple_click()
            await el.press("Control+a")
            await el.press("Delete")

            # Type with human-like delay
            await el.type(str(value), delay=_TYPE_DELAY)
            filled += 1
            await asyncio.sleep(0.1)   # small pause between fields

        except Exception as e:
            logger.warning(f"Failed to fill '{selector}': {e}")

    logger.info(f"Filled {filled}/{len(fill_plan)} fields.")
    return filled


async def upload_resume(
    page: Page,
    upload_selector: str,
    resume_bytes: bytes,
    filename: str = "resume.pdf",
) -> bool:
    """
    Upload the resume PDF to a file input element.
    Playwright requires writing to a temp file first.
    Returns True on success.
    """
    tmp_path = None
    try:
        # Write bytes to a temp file
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", prefix="ciaw_resume_", delete=False
        ) as tmp:
            tmp.write(resume_bytes)
            tmp_path = tmp.name

        el = await page.query_selector(upload_selector)
        if not el:
            logger.warning(f"Upload input not found: {upload_selector}")
            return False

        await el.set_input_files(tmp_path)
        logger.info(f"Resume uploaded via: {upload_selector}")

        # Wait for upload to register
        await asyncio.sleep(1.5)
        return True

    except Exception as e:
        logger.error(f"Resume upload failed: {e}")
        return False
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


async def click_submit(page: Page, submit_selector: str) -> bool:
    """
    Click the submit button and wait for navigation.
    Returns True if navigation succeeded (likely a confirmation page).
    """
    try:
        el = await page.query_selector(submit_selector)
        if not el:
            logger.warning("Submit button not found at click time.")
            return False

        logger.info(f"Clicking submit: {submit_selector}")
        async with page.expect_navigation(
            wait_until="networkidle", timeout=15000
        ):
            await el.click()

        logger.info(f"Post-submit URL: {page.url[:80]}")
        return True

    except Exception as e:
        logger.warning(f"Submit click/navigation issue (may be normal): {e}")
        # Some ATS use SPAs — no navigation event fires
        # Try clicking without waiting for navigation
        try:
            await page.click(submit_selector)
            await asyncio.sleep(3)
            return True
        except Exception:
            return False


async def is_confirmation_page(page: Page) -> bool:
    """
    Heuristic check: is the current page a submission confirmation?
    Looks for common thank-you/confirmation text patterns.
    """
    _CONFIRMATION_PHRASES = [
        "application submitted",
        "thank you for applying",
        "thanks for applying",
        "we've received your application",
        "successfully submitted",
        "application received",
        "you're being considered",
        "application complete",
    ]
    try:
        body = (await page.inner_text("body")).lower()
        for phrase in _CONFIRMATION_PHRASES:
            if phrase in body:
                logger.info(f"Confirmation page detected: '{phrase}'")
                return True
    except Exception:
        pass
    return False
