"""
Captcha Guard — Detects and handles CAPTCHAs during browser missions.

Detection targets:
  - reCAPTCHA v2/v3 (Google)
  - hCaptcha
  - Cloudflare Turnstile
  - Generic "robot check" patterns

On detection: pauses mission, logs to Firestore, alerts user via Zone B.
"""
from playwright.async_api import Page

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── CAPTCHA fingerprint selectors ────────────────────────────
_CAPTCHA_SELECTORS = [
    # reCAPTCHA
    "iframe[src*='recaptcha']",
    "iframe[src*='google.com/recaptcha']",
    ".g-recaptcha",
    "#recaptcha",
    # hCaptcha
    "iframe[src*='hcaptcha.com']",
    ".h-captcha",
    # Cloudflare Turnstile
    "iframe[src*='challenges.cloudflare.com']",
    ".cf-turnstile",
    # Generic patterns
    "[class*='captcha']",
    "[id*='captcha']",
    "iframe[title*='captcha' i]",
    "iframe[title*='challenge' i]",
]

# ── Page text patterns ────────────────────────────────────────
_CAPTCHA_TEXT_PATTERNS = [
    "prove you're not a robot",
    "verify you are human",
    "complete the captcha",
    "bot verification",
    "security check",
    "i'm not a robot",
]


async def detect_captcha(page: Page) -> bool:
    """
    Scan the current page DOM for known CAPTCHA indicators.
    Returns True if a CAPTCHA is detected.
    """
    # 1. Check for known CAPTCHA elements
    for selector in _CAPTCHA_SELECTORS:
        try:
            el = await page.query_selector(selector)
            if el:
                logger.warning(f"CAPTCHA detected via selector: {selector}")
                return True
        except Exception:
            continue

    # 2. Check page text content for CAPTCHA phrases
    try:
        body_text = (await page.inner_text("body")).lower()
        for pattern in _CAPTCHA_TEXT_PATTERNS:
            if pattern in body_text:
                logger.warning(f"CAPTCHA detected via text pattern: '{pattern}'")
                return True
    except Exception:
        pass

    return False


async def handle_captcha(
    page: Page,
    job_id: str,
    app_id: str,
    user_id: str,
) -> dict:
    """
    Called when a CAPTCHA is detected during a browser mission.

    Actions:
    1. Capture a screenshot of the blocked page
    2. Log manual_intervention_required to Firestore
    3. Return a structured error payload

    Returns a dict with status and details for the mission executor.
    """
    from app.utils.screenshot import capture_screenshot
    from app.db.thought_logs import write_thought_log

    logger.warning(f"CAPTCHA block — job_id={job_id} app_id={app_id}")

    # Capture screenshot of the CAPTCHA page
    screenshot_bytes = await capture_screenshot(page)

    # Write thought log alert to Zone B
    write_thought_log(
        user_id=user_id,
        message=(
            f"⚠️ CAPTCHA detected on job application page. "
            f"Manual intervention required. Application paused."
        ),
        log_type="Warning",
        job_id=job_id,
        app_id=app_id,
    )

    return {
        "status": "manual_intervention_required",
        "reason": "captcha_detected",
        "screenshot_bytes": screenshot_bytes,
        "job_id": job_id,
        "app_id": app_id,
    }
