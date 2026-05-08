"""
Recommendation Agent — USER SIDE
Ranks listings using deterministic composite scoring + Gemini semantic reasoning.
Returns sorted recommendations with scores and reasons.
"""
import json
from typing import Dict, Any, List
from app.services.gemini_service import generate_json
from app.utils.prompts import RECOMMENDATION_RANKING_PROMPT
from app.utils.scoring import compute_composite_score, build_score_reasons


async def run(user_preferences: Dict[str, Any], listings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Rank listings by relevance to user preferences.

    Input:
        user_preferences: Extracted preferences dict from preference_agent
        listings: List of listing dicts from search_agent

    Output:
        {
            "recommendations": [
                {
                    "listing_id": str,
                    "score": int,
                    "reasons": [...],
                    "concerns": [...]
                }
            ]
        }
    """
    if not listings:
        return {"recommendations": []}

    # Step 1: Deterministic composite scoring (fast, no LLM)
    scored = []
    for listing in listings:
        composite = compute_composite_score(listing, user_preferences)
        reasons = build_score_reasons(listing, user_preferences)
        scored.append({
            "listing_id": listing.get("id", ""),
            "score": int(composite),
            "reasons": reasons,
            "concerns": [],
            "_listing": listing,
        })

    # Sort deterministically by composite score (descending)
    scored.sort(key=lambda x: x["score"], reverse=True)

    # Step 2: Gemini semantic pass on top-5 for richer reasoning
    top_listings = [s["_listing"] for s in scored[:5]]
    top_ids = {l.get("id") for l in top_listings}

    try:
        prompt = RECOMMENDATION_RANKING_PROMPT.format(
            preferences=json.dumps(user_preferences, indent=2),
            listings=json.dumps(top_listings, indent=2),
        )
        gemini_result = await generate_json(prompt)
        gemini_recs = {
            r["listing_id"]: r
            for r in gemini_result.get("recommendations", [])
        }

        # Merge Gemini semantic reasons into scored results
        for item in scored:
            lid = item["listing_id"]
            if lid in gemini_recs:
                gem = gemini_recs[lid]
                # Boost score with Gemini's semantic score (average both)
                item["score"] = int((item["score"] + gem.get("score", item["score"])) / 2)
                item["reasons"] = list(set(item["reasons"] + gem.get("reasons", [])))
                item["concerns"] = gem.get("concerns", [])

    except Exception:
        pass  # Fall back to deterministic scores only

    # Remove internal _listing key before returning
    output = []
    for item in scored:
        item.pop("_listing", None)
        output.append(item)

    # Re-sort after merge
    output.sort(key=lambda x: x["score"], reverse=True)

    return {"recommendations": output}
