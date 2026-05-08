"""
USER SIDE Housing Routes
Handles: chat, search, recommend, negotiate, schedule
All routes are async and return strict JSON.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models.housing_models import (
    ChatRequest,
    SearchRequest,
    RecommendRequest,
    NegotiateRequest,
    ScheduleRequest,
)
from app.orchestrators import housing_orchestrator
from app.agents import (
    search_agent,
    recommendation_agent,
    negotiation_agent,
    scheduling_agent,
)

router = APIRouter(prefix="/api/housing", tags=["Housing - User Side"])


@router.post("/chat", summary="Chat Orchestrator")
async def chat(request: ChatRequest):
    """
    Main conversational entry point for the Housing Sub-Orchestrator.
    Classifies intent and routes to appropriate USER SIDE agents.
    Returns structured JSON with recommendations, search results, or action outputs.
    """
    try:
        result = await housing_orchestrator.handle_chat(
            query=request.query,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            history=request.history or [],
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e), "task": "chat"})


@router.post("/search", summary="Search Listings")
async def search(request: SearchRequest):
    """
    Direct housing search with structured filters.
    Does NOT use orchestrator — directly calls search agent.
    """
    try:
        result = await search_agent.run(
            budget=request.budget,
            location=request.location,
            property_type=request.property_type,
            bedrooms=request.bedrooms,
            furnishing=request.furnishing,
            occupancy=request.occupancy,
            preferences=request.preferences,
            page=request.page,
            page_size=request.page_size,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e), "task": "search"})


@router.post("/recommend", summary="Rank Recommendations")
async def recommend(request: RecommendRequest):
    """
    Rank provided listings against user preferences.
    Returns sorted recommendations with scores and reasons.
    """
    try:
        result = await recommendation_agent.run(
            user_preferences=request.user_preferences,
            listings=request.listings,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e), "task": "recommend"})


@router.post("/negotiate", summary="Generate Negotiation Strategy")
async def negotiate(request: NegotiateRequest):
    """
    Generate a professional rent negotiation message.
    Returns concise negotiation message with strategy.
    """
    try:
        result = await negotiation_agent.run(
            current_rent=request.current_rent,
            target_rent=request.target_rent,
            property_type=request.property_type or "flat",
            tenant_profile=request.tenant_profile or "working professional",
            language=request.language or "English",
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e), "task": "negotiate"})


@router.post("/schedule", summary="Schedule Property Visit")
async def schedule(request: ScheduleRequest):
    """
    Schedule a property visit.
    Checks for slot conflicts, writes to Firestore, sends Twilio reminder.
    """
    try:
        result = await scheduling_agent.run(
            property_id=request.property_id,
            user_id=request.user_id,
            slot=request.slot,
            notes=request.notes,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e), "task": "schedule"})
