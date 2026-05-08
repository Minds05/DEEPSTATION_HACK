"""
ADMIN SIDE Housing Routes
Handles: owner verification, fraud detection, agreement analysis.
These routes are INDEPENDENT — NOT connected to user orchestration flow.
"""
from fastapi import APIRouter, HTTPException
from app.models.admin_models import (
    VerificationRequest,
    FraudCheckRequest,
    AgreementAnalysisRequest,
)
from app.agents import (
    verification_agent,
    fraud_detection_agent,
    agreement_analysis_agent,
)

router = APIRouter(prefix="/api/admin", tags=["Housing - Admin Side"])


@router.post("/verify-owner", summary="Verify Property Owner")
async def verify_owner(request: VerificationRequest):
    """
    ADMIN: Verify owner identity via Aadhaar, PAN, selfie, and ownership documents.
    Uses OCR extraction, face matching, and Gemini analysis.
    Returns verification status and confidence score.
    """
    try:
        result = await verification_agent.run(
            owner_id=request.owner_id,
            listing_id=request.listing_id,
            aadhaar_image_b64=request.aadhaar_image_b64,
            pan_image_b64=request.pan_image_b64,
            selfie_b64=request.selfie_b64,
            utility_bill_b64=request.utility_bill_b64,
            ownership_proof_b64=request.ownership_proof_b64,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e), "task": "verify_owner"})


@router.post("/fraud-check", summary="Detect Listing Fraud")
async def fraud_check(request: FraudCheckRequest):
    """
    ADMIN: Detect fraud indicators in a listing.
    Checks image hashes, pricing anomalies, and contact metadata.
    Returns risk score and specific flags.
    """
    try:
        result = await fraud_detection_agent.run(
            listing_id=request.listing_id,
            listing_data=request.listing_data,
            image_b64_list=request.image_b64_list or [],
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e), "task": "fraud_check"})


@router.post("/analyze-agreement", summary="Analyze Rental Agreement")
async def analyze_agreement(request: AgreementAnalysisRequest):
    """
    ADMIN: Analyze a rental agreement PDF for risk clauses.
    Extracts text, identifies hidden clauses, deposit ambiguity, and suspicious terms.
    Returns risk assessment and specific issues found.
    """
    try:
        result = await agreement_analysis_agent.run(
            agreement_pdf_b64=request.agreement_pdf_b64,
            agreement_text=request.agreement_text,
            listing_id=request.listing_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e), "task": "analyze_agreement"})
