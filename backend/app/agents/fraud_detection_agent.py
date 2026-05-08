"""
Fraud Detection Agent — ADMIN SIDE
Detects suspicious rental listings via image hashing, pricing analysis, and Gemini Vision.
NOT connected to live user orchestration. Standalone admin API only.
"""
from typing import Dict, Any, List, Optional
import json
from app.services.gemini_service import generate_json, generate_json_with_image
from app.utils.prompts import FRAUD_DETECTION_PROMPT
from app.utils.image_utils import compute_phash, compute_md5, images_are_similar, decode_base64_image


# Known fraud listing hashes (would come from a persistent store in production)
_KNOWN_FRAUD_HASHES: set = set()


async def run(
    listing_id: str,
    listing_data: Dict[str, Any],
    image_b64_list: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    ADMIN ONLY: Analyze a listing for fraud indicators.

    Returns:
        {
            "risk_score": int,
            "risk_level": "low" | "medium" | "high" | "critical",
            "flags": [...],
            "analysis": {...},
            "recommendation": "approve" | "review" | "reject"
        }
    """
    flags = []
    image_concerns = []

    # ─── Image Analysis ───────────────────────────────────────
    if image_b64_list:
        image_hashes = []
        for idx, b64_img in enumerate(image_b64_list):
            try:
                img_bytes = decode_base64_image(b64_img)
                phash = compute_phash(img_bytes)
                md5 = compute_md5(img_bytes)

                # Check against known fraud hashes
                if md5 in _KNOWN_FRAUD_HASHES or phash in _KNOWN_FRAUD_HASHES:
                    flags.append("known_fraud_image_detected")
                    image_concerns.append(f"image_{idx} matches known fraud listing")

                # Check for duplicates within this listing
                for prev_hash in image_hashes:
                    if images_are_similar(phash, prev_hash, threshold=5):
                        flags.append("duplicate_image_detected")
                        image_concerns.append(f"image_{idx} is duplicate of a previous image")
                        break

                image_hashes.append(phash)

            except Exception as e:
                image_concerns.append(f"image_{idx} analysis failed: {str(e)}")

        # Gemini Vision analysis on first image if available
        if image_b64_list:
            try:
                img_bytes = decode_base64_image(image_b64_list[0])
                vision_prompt = (
                    "Analyze this property image. Return JSON: "
                    '{"looks_genuine": bool, "concerns": [list of concerns]}'
                )
                vision_result = await generate_json_with_image(vision_prompt, img_bytes)
                if not vision_result.get("looks_genuine", True):
                    image_concerns.extend(vision_result.get("concerns", []))
                    flags.append("image_quality_concern")
            except Exception:
                pass

    # ─── Pricing Anomaly Detection ────────────────────────────
    pricing_anomaly = False
    rent = listing_data.get("rent", 0)
    location = listing_data.get("location", "")
    property_type = listing_data.get("property_type", "")

    # Simple heuristic: extremely low rent for a location
    suspiciously_low_thresholds = {
        "Koramangala": 5000,
        "Indiranagar": 5000,
        "Whitefield": 4000,
        "Electronic City": 3000,
    }
    threshold = suspiciously_low_thresholds.get(location, 2000)
    if rent > 0 and rent < threshold:
        pricing_anomaly = True
        flags.append("suspiciously_low_pricing")

    # Unrealistically high rent for basic property
    if property_type == "PG" and rent > 50000:
        pricing_anomaly = True
        flags.append("unusually_high_rent_for_pg")

    # ─── Contact/Metadata Checks ──────────────────────────────
    contact_suspicious = False
    owner_phone = listing_data.get("owner_phone", "")
    description = listing_data.get("description", "")

    if not owner_phone or len(owner_phone) < 10:
        contact_suspicious = True
        flags.append("invalid_contact_number")

    # Check description quality
    desc_quality = "poor"
    if len(description) > 100:
        desc_quality = "good"
    elif len(description) > 30:
        desc_quality = "average"
    else:
        flags.append("thin_description")

    # ─── Gemini Fraud Analysis ────────────────────────────────
    try:
        prompt = FRAUD_DETECTION_PROMPT.format(
            listing_data=json.dumps(listing_data, indent=2)
        )
        gemini_result = await generate_json(prompt)
        gemini_flags = gemini_result.get("flags", [])
        flags.extend(gemini_flags)

        risk_score = gemini_result.get("risk_score", 0)
        risk_level = gemini_result.get("risk_level", "low")
        recommendation = gemini_result.get("recommendation", "approve")

    except Exception:
        # Fallback: calculate risk from local signals
        flag_count = len(set(flags))
        risk_score = min(100, flag_count * 20)
        risk_level = (
            "critical" if risk_score >= 80
            else "high" if risk_score >= 60
            else "medium" if risk_score >= 40
            else "low"
        )
        recommendation = (
            "reject" if risk_score >= 80
            else "review" if risk_score >= 40
            else "approve"
        )

    # Add image concerns from local analysis
    if image_concerns:
        all_concerns = image_concerns
    else:
        all_concerns = []

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "flags": list(set(flags)),
        "analysis": {
            "pricing_anomaly": pricing_anomaly,
            "description_quality": desc_quality,
            "contact_suspicious": contact_suspicious,
            "image_concerns": all_concerns,
        },
        "recommendation": recommendation,
    }
