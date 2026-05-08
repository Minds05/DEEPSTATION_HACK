"""
Pydantic models for admin-side agents.
These models are for independent admin workflows - NOT connected to live user routing.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


# ─── Enums ──────────────────────────────────────────────────
class VerificationStatus(str, Enum):
    verified = "verified"
    unverified = "unverified"
    requires_review = "requires_review"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AdminRecommendation(str, Enum):
    approve = "approve"
    manual_review = "manual_review"
    reject = "reject"


# ─── Verification Models ─────────────────────────────────────
class VerificationRequest(BaseModel):
    owner_id: str
    listing_id: Optional[str] = None
    aadhaar_image_b64: Optional[str] = Field(None, description="Base64 encoded Aadhaar card image")
    pan_image_b64: Optional[str] = Field(None, description="Base64 encoded PAN card image")
    selfie_b64: Optional[str] = Field(None, description="Base64 encoded selfie")
    utility_bill_b64: Optional[str] = Field(None, description="Base64 encoded utility bill")
    ownership_proof_b64: Optional[str] = Field(None, description="Base64 encoded ownership doc")


class DocumentCheckResult(BaseModel):
    aadhaar_valid: bool = False
    pan_valid: bool = False
    ownership_proof_consistent: bool = False
    face_match: Optional[bool] = None


class VerificationOutput(BaseModel):
    verification_status: VerificationStatus
    confidence_score: int = Field(..., ge=0, le=100)
    document_checks: DocumentCheckResult
    flags: List[str] = Field(default_factory=list)
    recommendation: AdminRecommendation


# ─── Fraud Detection Models ──────────────────────────────────
class FraudCheckRequest(BaseModel):
    listing_id: str
    listing_data: Dict[str, Any] = Field(..., description="Full listing details")
    image_b64_list: Optional[List[str]] = Field(
        default_factory=list, description="Base64 encoded property images"
    )


class FraudAnalysisDetail(BaseModel):
    pricing_anomaly: bool
    description_quality: str
    contact_suspicious: bool
    image_concerns: List[str] = Field(default_factory=list)


class FraudCheckOutput(BaseModel):
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    flags: List[str] = Field(default_factory=list)
    analysis: FraudAnalysisDetail
    recommendation: AdminRecommendation


# ─── Agreement Analysis Models ───────────────────────────────
class AgreementAnalysisRequest(BaseModel):
    listing_id: Optional[str] = None
    user_id: Optional[str] = None
    agreement_pdf_b64: Optional[str] = Field(None, description="Base64 encoded PDF")
    agreement_text: Optional[str] = Field(None, description="Raw text if already extracted")


class DepositAnalysis(BaseModel):
    amount_mentioned: bool
    refund_conditions_clear: bool
    deduction_rules_specified: bool


class TerminationAnalysis(BaseModel):
    notice_period_specified: bool
    early_exit_penalty_mentioned: bool


class AgreementAnalysisOutput(BaseModel):
    risk_level: RiskLevel
    overall_score: int = Field(..., ge=0, le=100)
    issues: List[str] = Field(default_factory=list)
    positive_clauses: List[str] = Field(default_factory=list)
    missing_clauses: List[str] = Field(default_factory=list)
    deposit_analysis: DepositAnalysis
    termination_analysis: TerminationAnalysis
    recommendation: str


# ─── Admin Queue Models ──────────────────────────────────────
class AdminQueueItem(BaseModel):
    item_id: str
    item_type: str  # "verification" | "fraud_check" | "agreement_analysis"
    listing_id: Optional[str] = None
    owner_id: Optional[str] = None
    status: str = "pending"  # "pending" | "in_review" | "completed"
    created_at: str
    assigned_to: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
