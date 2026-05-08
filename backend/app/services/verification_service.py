"""
Document verification service for admin-side verification workflows.
Handles OCR extraction, document validation, and face matching.
NOT connected to live user routing.
"""
import os
from typing import Dict, Optional, Any
import base64
import io

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False


def extract_text_from_image(image_bytes: bytes) -> str:
    """OCR extraction from image using Tesseract."""
    if not TESSERACT_AVAILABLE:
        return ""
    try:
        tesseract_path = os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        img = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(img, lang="eng")
        return text.strip()
    except Exception as e:
        return ""


def validate_aadhaar_text(text: str) -> Dict[str, Any]:
    """Validate Aadhaar card text for expected patterns."""
    import re
    result = {"valid": False, "aadhaar_number": None, "name_found": False}

    # Aadhaar is a 12-digit number (may appear as XXXX XXXX XXXX)
    pattern = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
    match = re.search(pattern, text)
    if match:
        result["valid"] = True
        result["aadhaar_number"] = match.group().replace(" ", "")

    # Check for common Aadhaar keywords
    if any(kw in text.upper() for kw in ["AADHAAR", "UNIQUE IDENTIFICATION", "UIDAI"]):
        result["name_found"] = True

    return result


def validate_pan_text(text: str) -> Dict[str, Any]:
    """Validate PAN card text for expected patterns."""
    import re
    result = {"valid": False, "pan_number": None}

    # PAN format: AAAAA1234A (5 letters, 4 digits, 1 letter)
    pattern = r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b'
    match = re.search(pattern, text)
    if match:
        result["valid"] = True
        result["pan_number"] = match.group()

    return result


def compare_faces(image1_bytes: bytes, image2_bytes: bytes) -> Dict[str, Any]:
    """
    Compare two face images for identity verification.
    Returns match confidence. Uses DeepFace if available.
    """
    if not DEEPFACE_AVAILABLE:
        return {"matched": None, "confidence": None, "error": "DeepFace not available"}

    try:
        result = DeepFace.verify(
            img1_path=image1_bytes,
            img2_path=image2_bytes,
            enforce_detection=False,
        )
        return {
            "matched": result.get("verified", False),
            "confidence": round((1 - result.get("distance", 1.0)) * 100, 2),
            "error": None,
        }
    except Exception as e:
        return {"matched": None, "confidence": None, "error": str(e)}


def decode_b64_image(b64_string: Optional[str]) -> Optional[bytes]:
    """Safely decode a base64 image string to bytes."""
    if not b64_string:
        return None
    try:
        if "," in b64_string:
            b64_string = b64_string.split(",", 1)[1]
        return base64.b64decode(b64_string)
    except Exception:
        return None
