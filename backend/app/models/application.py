"""
Application model — Pydantic schema for the applications collection.
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AppStatus(str, Enum):
    PENDING    = "pending"
    RUNNING    = "running"
    SUBMITTED  = "submitted"
    FAILED     = "failed"
    CAPTCHA    = "manual_intervention_required"
    SKIPPED    = "skipped"


class ApplicationRecord(BaseModel):
    app_id:           str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id:           str
    user_id:          str
    status:           AppStatus = AppStatus.PENDING
    match_score:      float = 0.0
    ats_type:         str = "unknown"
    timestamp:        Optional[datetime] = None
    screenshot_url:   Optional[str] = None
    cover_letter_url: Optional[str] = None
    error_log:        Optional[str] = None

    model_config = {"use_enum_values": False}
