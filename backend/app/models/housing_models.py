"""
Pydantic models for housing listings and user interactions.
All models enforce strict typing for machine-readable outputs.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum


# ─── Enums ──────────────────────────────────────────────────
class PropertyType(str, Enum):
    PG = "PG"
    flat = "flat"
    apartment = "apartment"
    room = "room"
    hostel = "hostel"


class FurnishingType(str, Enum):
    fully_furnished = "fully_furnished"
    semi_furnished = "semi_furnished"
    unfurnished = "unfurnished"


class OccupancyType(str, Enum):
    single = "single"
    shared = "shared"
    family = "family"


class GenderPreference(str, Enum):
    male = "male"
    female = "female"
    any = "any"


# ─── Request Models ──────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str = Field(..., description="User's natural language housing query")
    user_id: str = Field(..., description="Authenticated user ID")
    conversation_id: Optional[str] = Field(None)
    history: Optional[List[Dict[str, str]]] = Field(default_factory=list)


class SearchRequest(BaseModel):
    budget: Optional[int] = Field(None, ge=0)
    location: Optional[str] = None
    property_type: Optional[PropertyType] = None
    bedrooms: Optional[int] = Field(None, ge=0)
    furnishing: Optional[FurnishingType] = None
    occupancy: Optional[OccupancyType] = None
    gender_preference: Optional[GenderPreference] = None
    preferences: Optional[List[str]] = Field(default_factory=list)
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=50)


class RecommendRequest(BaseModel):
    user_preferences: Dict[str, Any] = Field(..., description="Extracted preferences dict")
    listings: List[Dict[str, Any]] = Field(..., description="Listings to rank")
    user_id: str


class NegotiateRequest(BaseModel):
    current_rent: int = Field(..., ge=0)
    target_rent: int = Field(..., ge=0)
    property_type: Optional[str] = "flat"
    tenant_profile: Optional[str] = "working professional"
    language: Optional[str] = "English"
    listing_id: Optional[str] = None


class ScheduleRequest(BaseModel):
    property_id: str
    user_id: str
    slot: str = Field(..., description="ISO 8601 datetime string, e.g. 2026-05-09T17:00:00")
    notes: Optional[str] = None


# ─── Response Models ─────────────────────────────────────────
class PreferenceOutput(BaseModel):
    budget: Optional[int] = None
    location: Optional[str] = None
    property_type: Optional[str] = None
    bedrooms: Optional[int] = None
    furnishing: Optional[str] = None
    occupancy: Optional[str] = None
    gender_preference: Optional[str] = None
    preferences: List[str] = Field(default_factory=list)
    nearby_requirements: List[str] = Field(default_factory=list)
    move_in_date: Optional[str] = None


class ListingItem(BaseModel):
    id: str
    title: str
    property_type: str
    rent: int
    location: str
    area: Optional[str] = None
    city: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    furnishing: Optional[str] = None
    amenities: List[str] = Field(default_factory=list)
    nearby: List[str] = Field(default_factory=list)
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    verified: bool = False
    available_from: Optional[str] = None
    occupancy: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[float] = None
    images: List[str] = Field(default_factory=list)
    gender_preference: Optional[str] = None


class SearchOutput(BaseModel):
    results: List[ListingItem]
    total: int
    page: int
    page_size: int
    source: str = Field("firestore", description="'firestore' or 'fallback'")


class RecommendationItem(BaseModel):
    listing_id: str
    score: int
    reasons: List[str]
    concerns: List[str] = Field(default_factory=list)


class RecommendOutput(BaseModel):
    recommendations: List[RecommendationItem]


class NegotiateOutput(BaseModel):
    message: str
    strategy: str
    fallback_rent: int
    key_points: List[str]


class ScheduleOutput(BaseModel):
    status: str
    visit_id: str
    property_id: str
    user_id: str
    slot: str
    notification_sent: bool = False


class ChatOutput(BaseModel):
    task: str
    response: Dict[str, Any]
    conversation_id: str
    agent_trace: List[str] = Field(default_factory=list)
