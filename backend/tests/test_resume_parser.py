"""
Unit Tests — Phase 2: Resume Parser
Tests the text extraction and Gemini output parsing logic.
"""
import pytest
import json
from app.agents.resume_parser import _extract_json
from app.utils.pdf_reader import _clean_text
from app.utils.logger import scrub_pii


# ── _extract_json tests ───────────────────────────────────────

def test_extract_json_plain():
    raw = '{"name": "John Doe", "skills": ["Python"]}'
    assert json.loads(_extract_json(raw))["name"] == "John Doe"


def test_extract_json_with_markdown_fences():
    raw = '```json\n{"name": "Jane", "skills": []}\n```'
    result = _extract_json(raw)
    assert json.loads(result)["name"] == "Jane"


def test_extract_json_with_preamble():
    raw = 'Here is the JSON:\n{"name": "Test", "skills": ["Go"]}'
    assert json.loads(_extract_json(raw))["name"] == "Test"


def test_extract_json_raises_on_no_json():
    with pytest.raises(ValueError):
        _extract_json("This response has no JSON object at all.")


# ── _clean_text tests ─────────────────────────────────────────

def test_clean_text_collapses_newlines():
    text = "Line 1\n\n\n\n\nLine 2"
    cleaned = _clean_text(text)
    assert "\n\n\n" not in cleaned
    assert "Line 1" in cleaned
    assert "Line 2" in cleaned


def test_clean_text_removes_null_bytes():
    text = "Hello\x00World\x01Test"
    cleaned = _clean_text(text)
    assert "\x00" not in cleaned
    assert "Hello" in cleaned


# ── PII scrub tests ───────────────────────────────────────────

def test_scrub_pii_removes_email():
    text = "Contact me at john.doe@example.com for details."
    result = scrub_pii(text)
    assert "john.doe@example.com" not in result
    assert "[EMAIL_REDACTED]" in result


def test_scrub_pii_removes_phone():
    text = "Call me at +91 98765 43210 anytime."
    result = scrub_pii(text)
    assert "98765" not in result
    assert "[PHONE_REDACTED]" in result


def test_scrub_pii_safe_text_unchanged():
    text = "I am a Senior Python Engineer with 6 years of experience."
    result = scrub_pii(text)
    assert result == text
