"""
Pydantic models for job listings, match results, and ATS detection.
"""
from __future__ import annotations
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ATSType(str, Enum):
    LEVER = "lever"
    GREENHOUSE = "greenhouse"
    WORKDAY = "workday"
    OTHER = "other"


class Decision(str, Enum):
    AUTO_APPLY = "AUTO_APPLY"
    MANUAL_REQUIRED = "MANUAL_REQUIRED"
    RECOMMENDATION = "RECOMMENDATION"


class JobListing(BaseModel):
    """Raw job data from search grounding."""
    job_id: Optional[str] = None
    title: str
    company: str
    url: str
    description_raw: str
    ats_type: ATSType
    discovered_at: Optional[datetime] = None


class MatchResult(BaseModel):
    """Output of scorer.py for a single job."""
    job_id: str
    match_score: float             # 0–100 combined score
    vector_score: float            # 40% component
    reasoning_score: float         # 60% component
    reasoning_summary: str         # Gemini explanation text
    decision: Decision


class JobSearchRequest(BaseModel):
    user_id: str
    role: Optional[str] = None
    location: Optional[str] = None
    remote: Optional[bool] = False
