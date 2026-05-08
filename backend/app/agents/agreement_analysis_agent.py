"""
Agreement Analysis Agent — ADMIN SIDE
Analyzes rental agreements for risky clauses, unclear deposits, and suspicious terms.
Uses PDF extraction + Gemini legal reasoning.
NOT connected to live user orchestration. Standalone admin API only.
"""
from typing import Dict, Any, Optional
import base64
from app.services.gemini_service import generate_json
from app.utils.prompts import AGREEMENT_ANALYSIS_PROMPT
from app.utils.pdf_utils import extract_pdf_text, get_pdf_metadata


async def run(
    agreement_pdf_b64: Optional[str] = None,
    agreement_text: Optional[str] = None,
    listing_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    ADMIN ONLY: Analyze a rental agreement for risks and issues.

    Returns:
        {
            "risk_level": "low" | "medium" | "high",
            "overall_score": int,
            "issues": [...],
            "positive_clauses": [...],
            "missing_clauses": [...],
            "deposit_analysis": {...},
            "termination_analysis": {...},
            "recommendation": str
        }
    """
    # ─── Extract text from PDF ────────────────────────────────
    extracted_text = agreement_text or ""

    if agreement_pdf_b64 and not extracted_text:
        try:
            # Decode base64 PDF
            if "," in agreement_pdf_b64:
                agreement_pdf_b64 = agreement_pdf_b64.split(",", 1)[1]
            pdf_bytes = base64.b64decode(agreement_pdf_b64)
            extracted_text = extract_pdf_text(pdf_bytes)
        except Exception as e:
            return {
                "risk_level": "high",
                "overall_score": 0,
                "issues": [f"Failed to extract PDF text: {str(e)}"],
                "positive_clauses": [],
                "missing_clauses": ["unable to process document"],
                "deposit_analysis": {
                    "amount_mentioned": False,
                    "refund_conditions_clear": False,
                    "deduction_rules_specified": False,
                },
                "termination_analysis": {
                    "notice_period_specified": False,
                    "early_exit_penalty_mentioned": False,
                },
                "recommendation": "Document could not be processed. Upload a valid PDF.",
            }

    if not extracted_text.strip():
        return {
            "risk_level": "high",
            "overall_score": 0,
            "issues": ["No text could be extracted from the document"],
            "positive_clauses": [],
            "missing_clauses": ["entire document content"],
            "deposit_analysis": {
                "amount_mentioned": False,
                "refund_conditions_clear": False,
                "deduction_rules_specified": False,
            },
            "termination_analysis": {
                "notice_period_specified": False,
                "early_exit_penalty_mentioned": False,
            },
            "recommendation": "Empty or unreadable document. Cannot analyze.",
        }

    # ─── Truncate for LLM (max 8000 chars) ───────────────────
    text_for_analysis = extracted_text[:8000]

    # ─── Gemini Legal Analysis ────────────────────────────────
    try:
        prompt = AGREEMENT_ANALYSIS_PROMPT.format(agreement_text=text_for_analysis)
        result = await generate_json(prompt)

        return {
            "risk_level": result.get("risk_level", "medium"),
            "overall_score": result.get("overall_score", 50),
            "issues": result.get("issues", []),
            "positive_clauses": result.get("positive_clauses", []),
            "missing_clauses": result.get("missing_clauses", []),
            "deposit_analysis": result.get("deposit_analysis", {
                "amount_mentioned": False,
                "refund_conditions_clear": False,
                "deduction_rules_specified": False,
            }),
            "termination_analysis": result.get("termination_analysis", {
                "notice_period_specified": False,
                "early_exit_penalty_mentioned": False,
            }),
            "recommendation": result.get("recommendation", "Manual review recommended"),
        }

    except Exception as e:
        # Fallback: basic keyword analysis
        text_lower = extracted_text.lower()
        issues = []
        positive = []

        if "refund" not in text_lower:
            issues.append("deposit refund condition unclear")
        if "notice period" not in text_lower:
            issues.append("notice period not specified")
        if "maintenance" not in text_lower:
            issues.append("maintenance responsibility not defined")

        if "tenant rights" in text_lower:
            positive.append("tenant rights mentioned")
        if "receipt" in text_lower:
            positive.append("receipt provision mentioned")

        return {
            "risk_level": "medium",
            "overall_score": 50,
            "issues": issues,
            "positive_clauses": positive,
            "missing_clauses": [],
            "deposit_analysis": {
                "amount_mentioned": "deposit" in text_lower,
                "refund_conditions_clear": "refund" in text_lower,
                "deduction_rules_specified": "deduction" in text_lower,
            },
            "termination_analysis": {
                "notice_period_specified": "notice" in text_lower,
                "early_exit_penalty_mentioned": "penalty" in text_lower,
            },
            "recommendation": f"Gemini analysis failed ({str(e)}). Basic checks applied.",
        }
