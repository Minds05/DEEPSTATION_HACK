"""
Screenshot Utility — Captures Playwright page screenshots as bytes.
Used for both confirmation captures and CAPTCHA/error captures.
"""
from playwright.async_api import Page
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def capture_screenshot(page: Page) -> bytes:
    """Capture a full-page screenshot and return raw PNG bytes."""
    try:
        png_bytes = await page.screenshot(full_page=True, type="png")
        logger.info(f"Screenshot captured: {len(png_bytes):,} bytes")
        return png_bytes
    except Exception as e:
        logger.error(f"Screenshot capture failed: {e}")
        return b""


async def capture_confirmation(page: Page) -> bytes:
    """
    Wait briefly for the confirmation page to fully render,
    then capture the full-page screenshot.
    """
    try:
        # Short wait for any post-submit animations to settle
        await page.wait_for_timeout(2000)
        return await capture_screenshot(page)
    except Exception as e:
        logger.error(f"Confirmation screenshot failed: {e}")
        return b""
