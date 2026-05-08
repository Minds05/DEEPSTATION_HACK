"""
Pydantic models for resume / user profile data.
"""
from __future__ import annotations
from pydantic import BaseModel, HttpUrl
from typing import Optional


class Project(BaseModel):
    title:        str            = ""
    description:  str            = ""
    impact:       Optional[str]  = None   # Gemini may omit this
    technologies: list[str]      = []


class Education(BaseModel):
    degree:      str          = ""
    institution: str          = ""
    year:        Optional[int] = None



class ResumeProfile(BaseModel):
    """Full parsed profile written to users/{userId}/profile."""
    name: str
    linkedin_url: Optional[str] = None
    skills: list[str]
    seniority: str                 # "Junior" | "Mid" | "Senior" | "Lead"
    years_experience: Optional[float] = None
    projects: list[Project] = []
    education: list[Education] = []
    resume_url: Optional[str] = None   # Firebase Storage path


class ParseResumeRequest(BaseModel):
    user_id: str


class ParseResumeResponse(BaseModel):
    user_id: str
    profile: ResumeProfile
    audit_message: str             # First Zone A chat message
