"""
Structured Logger — PII-safe.
Scrubs email and phone patterns before writing any log line.
All thought logs that go to Zone B must pass through this.
"""
import logging
import re
import sys

# ── PII scrub patterns ────────────────────────────────────────
_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
_PHONE_RE = re.compile(r'(\+?\d[\d\s\-().]{7,}\d)')


def scrub_pii(text: str) -> str:
    """Replace email and phone with masked tokens."""
    text = _EMAIL_RE.sub('[EMAIL_REDACTED]', text)
    text = _PHONE_RE.sub('[PHONE_REDACTED]', text)
    return text


class PIISafeFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record.msg = scrub_pii(str(record.msg))
        if record.args:
            record.args = tuple(scrub_pii(str(a)) for a in record.args) \
                if isinstance(record.args, tuple) else scrub_pii(str(record.args))
        return super().format(record)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger with PII-safe formatting."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(PIISafeFormatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S"
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
