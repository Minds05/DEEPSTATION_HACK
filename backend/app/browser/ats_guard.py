"""
ATS Guard — Detects Applicant Tracking System type from a job URL.

Supported classifications:
  LEVER       → lever.co (auto-apply eligible)
  GREENHOUSE  → greenhouse.io (auto-apply eligible)
  WORKDAY     → myworkdayjobs.com / workday.com (manual only)
  OTHER       → anything else (manual only)

Auto-apply is ONLY permitted for Lever and Greenhouse.
"""
import re
from urllib.parse import urlparse
from app.models.job import ATSType
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── ATS domain fingerprints ───────────────────────────────────
_ATS_PATTERNS: list[tuple[re.Pattern, ATSType]] = [
    # Lever
    (re.compile(r'(jobs\.lever\.co|lever\.co)', re.I), ATSType.LEVER),
    # Greenhouse
    (re.compile(r'(boards\.greenhouse\.io|greenhouse\.io)', re.I), ATSType.GREENHOUSE),
    # Workday variants
    (re.compile(r'(myworkdayjobs\.com|workday\.com|wd\d+\.myworkdayjobs\.com)', re.I), ATSType.WORKDAY),
    # iCIMS
    (re.compile(r'(icims\.com)', re.I), ATSType.OTHER),
    # SmartRecruiters
    (re.compile(r'(smartrecruiters\.com)', re.I), ATSType.OTHER),
    # BambooHR
    (re.compile(r'(bamboohr\.com)', re.I), ATSType.OTHER),
    # Taleo
    (re.compile(r'(taleo\.net)', re.I), ATSType.OTHER),
    # Ashby
    (re.compile(r'(ashbyhq\.com)', re.I), ATSType.OTHER),
    # Rippling
    (re.compile(r'(rippling\.com)', re.I), ATSType.OTHER),
]

_AUTO_APPLY_ELIGIBLE = {ATSType.LEVER, ATSType.GREENHOUSE}


def detect_ats(url: str) -> ATSType:
    """
    Classify a job URL into its ATS type.
    Checks the full URL string (not just domain) for robustness.
    """
    if not url:
        return ATSType.OTHER

    for pattern, ats_type in _ATS_PATTERNS:
        if pattern.search(url):
            logger.info(f"ATS detected: {ats_type.value} | URL: {url[:80]}")
            return ats_type

    # Fallback: check netloc for known keywords
    try:
        netloc = urlparse(url).netloc.lower()
        if "lever" in netloc:
            return ATSType.LEVER
        if "greenhouse" in netloc:
            return ATSType.GREENHOUSE
        if "workday" in netloc:
            return ATSType.WORKDAY
    except Exception:
        pass

    logger.info(f"ATS type: OTHER | URL: {url[:80]}")
    return ATSType.OTHER


def is_auto_apply_eligible(ats_type: ATSType) -> bool:
    """Returns True only for Lever and Greenhouse — the automatable ATS platforms."""
    return ats_type in _AUTO_APPLY_ELIGIBLE


def get_ats_label(ats_type: ATSType) -> str:
    """Human-readable label for display in Zone C job cards."""
    return {
        ATSType.LEVER:      "Lever ⚡",
        ATSType.GREENHOUSE: "Greenhouse ⚡",
        ATSType.WORKDAY:    "Workday ✍️",
        ATSType.OTHER:      "Other ✍️",
    }.get(ats_type, "Unknown")
