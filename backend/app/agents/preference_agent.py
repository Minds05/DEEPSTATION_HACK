"""
Preference Understanding Agent — USER SIDE
Extracts structured housing preferences from natural language queries.
Returns strict JSON only.
"""
from typing import Dict, Any
from app.services.gemini_service import generate_json
from app.utils.prompts import PREFERENCE_EXTRACTION_PROMPT


async def run(query: str) -> Dict[str, Any]:
    """
    Extract structured housing preferences from a user query.

    Input:
        query: Natural language housing requirement string.

    Output:
        {
            "budget": int | null,
            "location": str | null,
            "property_type": str | null,
            "preferences": [...],
            ...
        }
    """
    prompt = PREFERENCE_EXTRACTION_PROMPT.format(query=query)
    result = await generate_json(prompt)

    # Normalize: ensure all expected keys exist
    return {
        "budget": result.get("budget"),
        "location": result.get("location"),
        "property_type": result.get("property_type"),
        "bedrooms": result.get("bedrooms"),
        "furnishing": result.get("furnishing"),
        "occupancy": result.get("occupancy"),
        "gender_preference": result.get("gender_preference"),
        "preferences": result.get("preferences", []),
        "nearby_requirements": result.get("nearby_requirements", []),
        "move_in_date": result.get("move_in_date"),
    }
