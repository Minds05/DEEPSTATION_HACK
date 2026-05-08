"""
DOM Mapper — Maps Firestore user profile fields to HTML form field IDs.

Lever and Greenhouse use predictable field name conventions.
This module:
  1. Scans the DOM for known field patterns
  2. Maps profile data to each discovered field
  3. Returns a fill plan: {selector: value}

Handles both input[type=text] and select elements.
"""
from playwright.async_api import Page
from typing import Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Field pattern definitions ─────────────────────────────────
# Each entry: (css_selector_patterns, profile_key, transform_fn)
# Tried in order; first match wins.

_FIELD_MAP = [
    # ── Personal ──────────────────────────────────────────────
    {
        "patterns": [
            "input[name*='first_name' i]", "input[id*='first_name' i]",
            "input[placeholder*='first name' i]", "input[autocomplete='given-name']",
        ],
        "key": "first_name",
    },
    {
        "patterns": [
            "input[name*='last_name' i]", "input[id*='last_name' i]",
            "input[placeholder*='last name' i]", "input[autocomplete='family-name']",
        ],
        "key": "last_name",
    },
    {
        "patterns": [
            "input[name*='full_name' i]", "input[id*='full_name' i]",
            "input[placeholder*='full name' i]", "input[autocomplete='name']",
            "input[name='name']", "input[id='name']",
        ],
        "key": "full_name",
    },
    {
        "patterns": [
            "input[type='email']", "input[name*='email' i]",
            "input[id*='email' i]", "input[autocomplete='email']",
        ],
        "key": "email",
    },
    {
        "patterns": [
            "input[type='tel']", "input[name*='phone' i]",
            "input[id*='phone' i]", "input[autocomplete='tel']",
            "input[placeholder*='phone' i]",
        ],
        "key": "phone",
    },
    # ── Professional ──────────────────────────────────────────
    {
        "patterns": [
            "input[name*='linkedin' i]", "input[id*='linkedin' i]",
            "input[placeholder*='linkedin' i]",
        ],
        "key": "linkedin_url",
    },
    {
        "patterns": [
            "input[name*='website' i]", "input[id*='website' i]",
            "input[name*='portfolio' i]", "input[placeholder*='website' i]",
        ],
        "key": "linkedin_url",   # fallback to LinkedIn URL if no portfolio
    },
    # ── Location ──────────────────────────────────────────────
    {
        "patterns": [
            "input[name*='location' i]", "input[id*='location' i]",
            "input[placeholder*='city' i]", "input[autocomplete='address-level2']",
        ],
        "key": "location",
    },
]

# ── Cover letter / additional info textarea ───────────────────
_TEXTAREA_MAP = [
    {
        "patterns": [
            "textarea[name*='cover' i]", "textarea[id*='cover' i]",
            "textarea[placeholder*='cover letter' i]",
            "textarea[name*='additional' i]", "textarea[id*='additional' i]",
        ],
        "key": "cover_letter",
    },
    {
        "patterns": [
            "textarea[name*='message' i]", "textarea[id*='message' i]",
            "textarea[placeholder*='tell us' i]", "textarea[placeholder*='about yourself' i]",
        ],
        "key": "summary",
    },
]

# ── File upload selector for resume ──────────────────────────
_RESUME_SELECTORS = [
    "input[type='file'][name*='resume' i]",
    "input[type='file'][id*='resume' i]",
    "input[type='file'][name*='cv' i]",
    "input[type='file'][accept*='pdf' i]",
    "input[type='file']",
]


def _split_name(full_name: str) -> tuple[str, str]:
    """Split 'John Doe Smith' → ('John', 'Doe Smith')."""
    parts = (full_name or "").strip().split(" ", 1)
    return parts[0], parts[1] if len(parts) > 1 else ""


async def build_fill_plan(
    page: Page,
    profile: dict,
    cover_letter: Optional[str] = None,
) -> dict[str, str]:
    """
    Scan the current page DOM and return a fill plan:
    { css_selector: value_to_type }

    Args:
        page:          Active Playwright page
        profile:       Firestore user profile dict
        cover_letter:  Optional cover letter text for textarea fields
    """
    first_name, last_name = _split_name(profile.get("name", ""))

    # Resolve all values from profile
    value_map = {
        "first_name":   first_name,
        "last_name":    last_name,
        "full_name":    profile.get("name", ""),
        "email":        profile.get("email", ""),
        "phone":        profile.get("phone", ""),
        "linkedin_url": profile.get("linkedin_url", ""),
        "location":     profile.get("location", ""),
        "cover_letter": cover_letter or "",
        "summary":      (
            f"Experienced {profile.get('seniority', '')} engineer with "
            f"{profile.get('years_experience', '')} years of experience "
            f"in {', '.join((profile.get('skills') or [])[:3])}."
        ),
    }

    fill_plan: dict[str, str] = {}

    # ── Scan input fields ─────────────────────────────────────
    for field_def in _FIELD_MAP:
        value = value_map.get(field_def["key"], "")
        if not value:
            continue
        for selector in field_def["patterns"]:
            try:
                el = await page.query_selector(selector)
                if el and await el.is_visible():
                    fill_plan[selector] = value
                    break   # first match wins
            except Exception:
                continue

    # ── Scan textareas ────────────────────────────────────────
    for field_def in _TEXTAREA_MAP:
        value = value_map.get(field_def["key"], "")
        if not value:
            continue
        for selector in field_def["patterns"]:
            try:
                el = await page.query_selector(selector)
                if el and await el.is_visible():
                    fill_plan[selector] = value
                    break
            except Exception:
                continue

    logger.info(f"DOM map complete: {len(fill_plan)} fields found on page.")
    return fill_plan


async def find_resume_upload_input(page: Page) -> Optional[str]:
    """Return the CSS selector of the first visible file upload input, or None."""
    for selector in _RESUME_SELECTORS:
        try:
            el = await page.query_selector(selector)
            if el:
                logger.info(f"Resume upload input found: {selector}")
                return selector
        except Exception:
            continue
    logger.warning("No resume upload input found on page.")
    return None


async def find_submit_button(page: Page) -> Optional[str]:
    """
    Find the primary form submit button.
    Returns a CSS selector string or None.
    """
    candidates = [
        "button[type='submit']",
        "input[type='submit']",
        "button:has-text('Submit Application')",
        "button:has-text('Submit')",
        "button:has-text('Apply')",
        "button:has-text('Apply Now')",
        "button:has-text('Send Application')",
        "[data-qa='btn-submit']",
        ".submit-btn", "#submit-btn",
    ]
    for selector in candidates:
        try:
            el = await page.query_selector(selector)
            if el and await el.is_visible() and await el.is_enabled():
                logger.info(f"Submit button found: {selector}")
                return selector
        except Exception:
            continue
    logger.warning("Submit button not found.")
    return None
