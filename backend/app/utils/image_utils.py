"""
Image utility functions for fraud detection and property verification.
Provides image hashing and comparison utilities.
"""
import hashlib
from typing import Optional
import imagehash
from PIL import Image
import io
import base64


def compute_phash(image_bytes: bytes) -> str:
    """Compute perceptual hash for duplicate image detection."""
    img = Image.open(io.BytesIO(image_bytes))
    return str(imagehash.phash(img))


def compute_dhash(image_bytes: bytes) -> str:
    """Compute difference hash for similarity detection."""
    img = Image.open(io.BytesIO(image_bytes))
    return str(imagehash.dhash(img))


def compute_md5(image_bytes: bytes) -> str:
    """Compute MD5 hash for exact duplicate detection."""
    return hashlib.md5(image_bytes).hexdigest()


def images_are_similar(hash1: str, hash2: str, threshold: int = 10) -> bool:
    """
    Compare two perceptual hashes.
    threshold: max hamming distance to consider images similar (lower = stricter).
    """
    try:
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)
        return (h1 - h2) <= threshold
    except Exception:
        return False


def decode_base64_image(b64_string: str) -> bytes:
    """Decode base64 image string to bytes."""
    if "," in b64_string:
        b64_string = b64_string.split(",", 1)[1]
    return base64.b64decode(b64_string)


def image_to_base64(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """Convert image bytes to base64 data URI."""
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"


def resize_image_for_api(image_bytes: bytes, max_size: int = 1024) -> bytes:
    """Resize image for Gemini Vision API (keeps aspect ratio)."""
    img = Image.open(io.BytesIO(image_bytes))
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=85)
    return output.getvalue()
