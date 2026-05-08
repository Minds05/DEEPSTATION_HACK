"""
Housing Sub-Orchestrator
Receives housing requests, classifies the subtask, routes to USER SIDE agents only,
combines outputs, and returns structured JSON.

Architecture:
    Main Orchestrator
        └── Housing Sub-Orchestrator  ← THIS FILE
                ├── Preference Understanding Agent
                ├── Housing Search Agent
                ├── Recommendation Agent
                ├── Negotiation Agent
                └── Scheduling Agent

Admin agents (Verification, Fraud Detection, Agreement Analysis)
are NOT routed through this orchestrator.
"""
import uuid
import json
from typing import Dict, Any, List, Optional
from app.services.gemini_service import generate_json
from app.services.firestore_service import log_interaction
from app.utils.prompts import ORCHESTRATOR_CLASSIFICATION_PROMPT

# USER SIDE agents — only these are imported for live routing
from app.agents import (
    preference_agent,
    search_agent,
    recommendation_agent,
    negotiation_agent,
    scheduling_agent,
)


async def handle_chat(
    query: str,
    user_id: str,
    conversation_id: Optional[str] = None,
    history: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Main entry point for the Housing Sub-Orchestrator.

    Flow:
        1. Classify the user's intent (task type)
        2. Route to the appropriate USER SIDE agents
        3. Combine agent outputs
        4. Return structured JSON

    Returns strict JSON — no greetings, no markdown, no decorative text.
    """
    conv_id = conversation_id or str(uuid.uuid4())
    history = history or []
    agent_trace = []

    # ─── Step 1: Classify intent ─────────────────────────────
    try:
        classification_prompt = ORCHESTRATOR_CLASSIFICATION_PROMPT.format(
            query=query,
            history=json.dumps(history[-5:], indent=2),  # Last 5 turns
        )
        classification = await generate_json(classification_prompt)
    except Exception as e:
        # Fallback: default to search+recommend flow
        classification = {
            "task": "recommend",
            "confidence": 60,
            "extracted_params": {},
            "requires_agents": ["preference", "search", "recommendation"],
            "response_required": True,
        }
        agent_trace.append(f"classification_fallback: {str(e)}")

    task = classification.get("task", "recommend")
    params = classification.get("extracted_params", {})
    agent_trace.append(f"classified_task: {task}")

    # ─── Step 2: Route to USER SIDE agents ───────────────────
    response_data = {}

    if task in ("search", "recommend", "general_query"):
        # Always extract preferences first
        agent_trace.append("preference_agent:start")
        preferences = await preference_agent.run(query)
        agent_trace.append("preference_agent:done")

        # Merge any explicitly extracted params from classification
        for key, val in params.items():
            if val and not preferences.get(key):
                preferences[key] = val

        # Search listings based on preferences
        agent_trace.append("search_agent:start")
        search_result = await search_agent.run(
            budget=preferences.get("budget"),
            location=preferences.get("location"),
            property_type=preferences.get("property_type"),
            bedrooms=preferences.get("bedrooms"),
            furnishing=preferences.get("furnishing"),
            occupancy=preferences.get("occupancy"),
            preferences=preferences.get("preferences", []),
        )
        agent_trace.append(f"search_agent:done ({search_result['total']} results)")

        if task == "recommend" or len(search_result["results"]) > 0:
            # Rank results via recommendation agent
            agent_trace.append("recommendation_agent:start")
            rec_result = await recommendation_agent.run(
                user_preferences=preferences,
                listings=search_result["results"],
            )
            agent_trace.append("recommendation_agent:done")

            response_data = {
                "preferences": preferences,
                "search": search_result,
                "recommendations": rec_result,
            }
        else:
            response_data = {
                "preferences": preferences,
                "search": search_result,
                "recommendations": {"recommendations": []},
            }

    elif task == "negotiate":
        listing_id = params.get("listing_id")
        current_rent = int(params.get("budget", 0) * 1.15) if params.get("budget") else 15000
        target_rent = params.get("budget") or 12000

        agent_trace.append("negotiation_agent:start")
        neg_result = await negotiation_agent.run(
            current_rent=current_rent,
            target_rent=target_rent,
        )
        agent_trace.append("negotiation_agent:done")

        response_data = {"negotiation": neg_result}

    elif task == "schedule":
        property_id = params.get("listing_id", "")
        slot = params.get("slot", "")

        if property_id and slot:
            agent_trace.append("scheduling_agent:start")
            sched_result = await scheduling_agent.run(
                property_id=property_id,
                user_id=user_id,
                slot=slot,
            )
            agent_trace.append("scheduling_agent:done")
            response_data = {"schedule": sched_result}
        else:
            response_data = {
                "error": "property_id and slot required for scheduling",
                "task": "schedule",
            }

    else:
        # Unknown task — default to preference+search
        agent_trace.append("fallback:preference+search")
        preferences = await preference_agent.run(query)
        search_result = await search_agent.run(
            budget=preferences.get("budget"),
            location=preferences.get("location"),
        )
        response_data = {
            "preferences": preferences,
            "search": search_result,
        }

    # ─── Step 3: Log interaction to Firestore ─────────────────
    await log_interaction({
        "conversation_id": conv_id,
        "user_id": user_id,
        "query": query,
        "task": task,
        "agent_trace": agent_trace,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    })

    return {
        "task": task,
        "response": response_data,
        "conversation_id": conv_id,
        "agent_trace": agent_trace,
    }
