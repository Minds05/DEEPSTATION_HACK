"""
Browser Controller — Playwright Async Session Manager

Manages a pool of isolated browser contexts.
Each auto-apply mission gets its own context so parallel runs
don't interfere with each other's cookies/storage.
"""
import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
)

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Module-level singleton ─────────────────────────────────────
_playwright: Optional[Playwright] = None
_browser: Optional[Browser] = None
_lock = asyncio.Lock()


async def _ensure_browser() -> Browser:
    """Lazily launch Chromium browser (singleton). Thread-safe."""
    global _playwright, _browser
    async with _lock:
        if _browser is None or not _browser.is_connected():
            logger.info("Launching Playwright Chromium browser...")
            _playwright = await async_playwright().start()
            _browser = await _playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                ],
            )
            logger.info("Browser launched.")
    return _browser


async def close_browser() -> None:
    """Gracefully close the browser and Playwright instance."""
    global _playwright, _browser
    if _browser:
        await _browser.close()
        _browser = None
    if _playwright:
        await _playwright.stop()
        _playwright = None
    logger.info("Browser closed.")


@asynccontextmanager
async def new_browser_context(user_agent: Optional[str] = None):
    """
    Async context manager that yields an isolated BrowserContext.
    Automatically closes the context on exit.

    Usage:
        async with new_browser_context() as (context, page):
            await page.goto(url)
    """
    browser = await _ensure_browser()

    ua = user_agent or (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    context: BrowserContext = await browser.new_context(
        user_agent=ua,
        viewport={"width": 1280, "height": 900},
        locale="en-US",
        timezone_id="Asia/Kolkata",
        # Prevent bot detection
        extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
    )

    # Stealth: remove webdriver property
    await context.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    page: Page = await context.new_page()
    logger.info("New browser context created.")

    try:
        yield context, page
    finally:
        await context.close()
        logger.info("Browser context closed.")


async def navigate(page: Page, url: str, timeout: int = 30000) -> bool:
    """
    Navigate to a URL and wait for network idle.
    Returns True on success, False on timeout/error.
    """
    try:
        await page.goto(url, wait_until="networkidle", timeout=timeout)
        logger.info(f"Navigated to: {url[:80]}")
        return True
    except Exception as e:
        logger.warning(f"Navigation failed for {url[:80]}: {e}")
        return False
