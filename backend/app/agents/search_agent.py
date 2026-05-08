"""
Housing Search Agent — USER SIDE
Searches listings in Firestore or falls back to housing.json.
Returns paginated, filtered results.
"""
from typing import Dict, Any, Optional
from app.services.firestore_service import get_listings


async def run(
    budget: Optional[int] = None,
    location: Optional[str] = None,
    property_type: Optional[str] = None,
    bedrooms: Optional[int] = None,
    furnishing: Optional[str] = None,
    occupancy: Optional[str] = None,
    preferences: Optional[list] = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    """
    Search housing listings with structured filters.

    Input params map directly from extracted preferences.

    Output:
        {
            "results": [...],
            "total": int,
            "page": int,
            "page_size": int,
            "source": "firestore" | "fallback"
        }
    """
    data = await get_listings(
        budget=budget,
        location=location,
        property_type=property_type,
        page=page,
        page_size=page_size,
    )

    results = data.get("results", [])

    # Additional in-memory filtering for fields not supported in Firestore query
    if furnishing:
        results = [r for r in results if r.get("furnishing") == furnishing]
    if occupancy:
        results = [r for r in results if r.get("occupancy") == occupancy]
    if bedrooms is not None:
        results = [r for r in results if r.get("bedrooms") == bedrooms]

    return {
        "results": results,
        "total": len(results),
        "page": page,
        "page_size": page_size,
        "source": data.get("source", "fallback"),
    }
