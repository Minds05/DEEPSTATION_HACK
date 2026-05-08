"""
Verification Agent — ADMIN SIDE
Verifies owner identity and property ownership via document OCR and face matching.
NOT connected to live user orchestration. Standalone admin API only.
"""
from typing import Dict, Any, Optional
from app.services.gemini_service import generate_json
from app.services.verification_service import (
    extract_text_from_image,
    validate_aadhaar_text,
    validate_pan_text,
    compare_faces,
    decode_b64_image,
)
from app.utils.prompts import VERIFICATION_PROMPT
import json


async def run(
    owner_id: str,
    listing_id: Optional[str] = None,
    aadhaar_image_b64: Optional[str] = None,
    pan_image_b64: Optional[str] = None,
    selfie_b64: Optional[str] = None,
    utility_bill_b64: Optional[str] = None,
    ownership_proof_b64: Optional[str] = None,
) -> Dict[str, Any]:
    """
    ADMIN ONLY: Verify owner identity and property documents.

    Returns:
        {
            "verification_status": "verified" | "unverified" | "requires_review",
            "confidence_score": int,
            "document_checks": {...},
            "flags": [...],
            "recommendation": "approve" | "manual_review" | "reject"
        }
    """
    document_data = {}
    checks = {
        "aadhaar_valid": False,
        "pan_valid": False,
        "ownership_proof_consistent": False,
        "face_match": None,
    }
    flags = []

    # ─── Aadhaar OCR ─────────────────────────────────────────
    if aadhaar_image_b64:
        aadhaar_bytes = decode_b64_image(aadhaar_image_b64)
        if aadhaar_bytes:
            text = extract_text_from_image(aadhaar_bytes)
            validation = validate_aadhaar_text(text)
            checks["aadhaar_valid"] = validation["valid"]
            document_data["aadhaar_ocr"] = text[:500]  # Trim for LLM
            if not validation["valid"]:
                flags.append("aadhaar_number_not_detected")
        else:
            flags.append("aadhaar_image_decode_failed")

    # ─── PAN OCR ─────────────────────────────────────────────
    if pan_image_b64:
        pan_bytes = decode_b64_image(pan_image_b64)
        if pan_bytes:
            text = extract_text_from_image(pan_bytes)
            validation = validate_pan_text(text)
            checks["pan_valid"] = validation["valid"]
            document_data["pan_ocr"] = text[:300]
            if not validation["valid"]:
                flags.append("pan_number_not_detected")
        else:
            flags.append("pan_image_decode_failed")

    # ─── Face Match (selfie vs Aadhaar) ──────────────────────
    if selfie_b64 and aadhaar_image_b64:
        selfie_bytes = decode_b64_image(selfie_b64)
        aadhaar_bytes = decode_b64_image(aadhaar_image_b64)
        if selfie_bytes and aadhaar_bytes:
            face_result = compare_faces(aadhaar_bytes, selfie_bytes)
            checks["face_match"] = face_result.get("matched")
            if face_result.get("matched") is False:
                flags.append("face_mismatch_detected")
            if face_result.get("error"):
                flags.append(f"face_check_error: {face_result['error']}")

    # ─── Ownership Proof ──────────────────────────────────────
    if ownership_proof_b64:
        proof_bytes = decode_b64_image(ownership_proof_b64)
        if proof_bytes:
            text = extract_text_from_image(proof_bytes)
            document_data["ownership_ocr"] = text[:500]
            checks["ownership_proof_consistent"] = len(text) > 50  # Basic validation
        else:
            flags.append("ownership_proof_decode_failed")

    # ─── Gemini Verification Analysis ────────────────────────
    try:
        prompt = VERIFICATION_PROMPT.format(
            document_data=json.dumps(document_data, indent=2)
        )
        gemini_result = await generate_json(prompt)

        # Merge Gemini insights with local checks
        gemini_flags = gemini_result.get("flags", [])
        flags.extend(gemini_flags)

        verification_status = gemini_result.get("verification_status", "requires_review")
        confidence_score = gemini_result.get("confidence_score", 50)
        recommendation = gemini_result.get("recommendation", "manual_review")

        # Override with local document check results
        doc_checks = gemini_result.get("document_checks", {})
        checks["aadhaar_valid"] = checks["aadhaar_valid"] or doc_checks.get("aadhaar_valid", False)
        checks["pan_valid"] = checks["pan_valid"] or doc_checks.get("pan_valid", False)

    except Exception as e:
        # Fallback to local analysis only
        verified_docs = sum([
            checks["aadhaar_valid"],
            checks["pan_valid"],
            checks["ownership_proof_consistent"],
        ])
        confidence_score = int((verified_docs / 3) * 80)
        verification_status = "verified" if verified_docs >= 2 else "requires_review"
        recommendation = "approve" if verified_docs >= 2 else "manual_review"
        flags.append(f"gemini_unavailable: {str(e)}")

    return {
        "verification_status": verification_status,
        "confidence_score": confidence_score,
        "document_checks": checks,
        "flags": list(set(flags)),
        "recommendation": recommendation,
    }
