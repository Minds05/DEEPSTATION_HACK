"""
Gemini AI service for all agent LLM calls.
Centralizes model configuration, retry logic, and JSON parsing.
"""
import os
import json
import re
from typing import Any, Dict, Optional
import google.generativeai as genai


# ─── Initialization ──────────────────────────────────────────
_key_index = 0

def _get_next_api_key() -> str:
    global _key_index
    keys = []
    key1 = os.getenv("GEMINI_API_KEY")
    key2 = os.getenv("GEMINI_API_KEY_2")
    if key1: keys.append(key1)
    if key2: keys.append(key2)
    if not keys:
        raise ValueError("No GEMINI_API_KEY or GEMINI_API_KEY_2 environment variable is set")
    
    key = keys[_key_index % len(keys)]
    _key_index += 1
    return key

def _get_gemini_model() -> Any:
    """Initialize Gemini client with alternating API keys."""
    api_key = _get_next_api_key()
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=genai.types.GenerationConfig(
            temperature=0.2,
            response_mime_type="application/json",
        ),
    )


def _get_vision_model() -> Any:
    """Initialize Gemini Vision model for image analysis with alternating API keys."""
    api_key = _get_next_api_key()
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=genai.types.GenerationConfig(
            temperature=0.2,
        ),
    )


# ─── Core Generation ─────────────────────────────────────────
async def generate_json(prompt: str) -> Dict[str, Any]:
    """
    Generate a JSON response from Gemini 2.5 Flash.
    Returns parsed dict. Raises ValueError on invalid JSON.
    """
    model = _get_gemini_model()
    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        return _parse_json_response(raw)
    except Exception as e:
        raise RuntimeError(f"Gemini generation failed: {str(e)}")


async def generate_json_with_image(prompt: str, image_bytes: bytes, mime_type: str = "image/jpeg") -> Dict[str, Any]:
    """
    Generate a JSON response with image input (Gemini Vision).
    """
    model = _get_vision_model()
    try:
        import google.generativeai as genai
        image_part = {"mime_type": mime_type, "data": image_bytes}
        response = model.generate_content([prompt, image_part])
        raw = response.text.strip()
        return _parse_json_response(raw)
    except Exception as e:
        raise RuntimeError(f"Gemini vision generation failed: {str(e)}")


def _parse_json_response(raw: str) -> Dict[str, Any]:
    """
    Parse JSON from Gemini response.
    Handles markdown code fences if present.
    """
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        # Attempt to extract JSON object from response
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
        raise ValueError(f"Failed to parse JSON from Gemini: {e}. Raw: {raw[:200]}")
