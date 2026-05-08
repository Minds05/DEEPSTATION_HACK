"""
Scoring utilities for housing recommendation ranking.
Provides deterministic score calculations before Gemini semantic pass.
"""
from typing import Dict, Any, List


def compute_budget_score(listing_rent: int, user_budget: int) -> float:
    """Returns 0-100 score based on how well the rent fits budget."""
    if listing_rent > user_budget:
        # Over budget: penalize proportionally
        overage = (listing_rent - user_budget) / user_budget
        return max(0.0, 50.0 - (overage * 100))
    # Under budget: full score with bonus for savings
    savings_ratio = (user_budget - listing_rent) / user_budget
    return min(100.0, 80.0 + (savings_ratio * 20))


def compute_location_score(listing_location: str, preferred_location: str) -> float:
    """Returns 0-100 score for location match (exact or partial)."""
    if not listing_location or not preferred_location:
        return 50.0
    l1 = listing_location.lower().strip()
    l2 = preferred_location.lower().strip()
    if l1 == l2:
        return 100.0
    if l1 in l2 or l2 in l1:
        return 75.0
    return 30.0


def compute_amenity_score(listing_amenities: List[str], preferred_features: List[str]) -> float:
    """Returns 0-100 score based on amenity overlap."""
    if not preferred_features:
        return 70.0  # Neutral if no preferences
    if not listing_amenities:
        return 20.0
    matched = sum(1 for p in preferred_features if p.lower() in [a.lower() for a in listing_amenities])
    return min(100.0, (matched / len(preferred_features)) * 100)


def compute_property_type_score(listing_type: str, preferred_type: str) -> float:
    """Returns 0 or 100 for exact match, 50 for compatible types."""
    if not preferred_type:
        return 70.0
    if listing_type.lower() == preferred_type.lower():
        return 100.0
    compatible = {
        "flat": ["apartment"],
        "apartment": ["flat"],
        "PG": ["hostel", "room"],
        "hostel": ["PG"],
    }
    if preferred_type in compatible.get(listing_type, []):
        return 60.0
    return 0.0


def compute_composite_score(listing: Dict[str, Any], preferences: Dict[str, Any]) -> float:
    """
    Weighted composite score from multiple signals.
    Weights: budget 40%, location 30%, amenities 20%, type 10%
    """
    budget_score = 0.0
    location_score = 0.0
    amenity_score = 0.0
    type_score = 0.0

    if preferences.get("budget"):
        budget_score = compute_budget_score(listing.get("rent", 0), preferences["budget"])
    else:
        budget_score = 70.0  # Neutral

    if preferences.get("location"):
        location_score = compute_location_score(
            listing.get("location", ""), preferences["location"]
        )
    else:
        location_score = 70.0

    all_preferences = (preferences.get("preferences", []) or []) + (
        preferences.get("nearby_requirements", []) or []
    )
    amenity_score = compute_amenity_score(
        listing.get("amenities", []) + listing.get("nearby", []), all_preferences
    )

    if preferences.get("property_type"):
        type_score = compute_property_type_score(
            listing.get("property_type", ""), preferences["property_type"]
        )
    else:
        type_score = 70.0

    composite = (
        budget_score * 0.40
        + location_score * 0.30
        + amenity_score * 0.20
        + type_score * 0.10
    )
    return round(composite, 2)


def build_score_reasons(listing: Dict[str, Any], preferences: Dict[str, Any]) -> List[str]:
    """Generate human-readable reasons for a listing's score."""
    reasons = []

    if preferences.get("budget") and listing.get("rent"):
        if listing["rent"] <= preferences["budget"]:
            savings = preferences["budget"] - listing["rent"]
            reasons.append(f"within budget (saves ₹{savings}/month)")
        else:
            reasons.append(f"slightly over budget by ₹{listing['rent'] - preferences['budget']}")

    if preferences.get("location"):
        if preferences["location"].lower() in listing.get("location", "").lower():
            reasons.append(f"matches preferred location: {listing['location']}")

    if preferences.get("property_type"):
        if listing.get("property_type", "").lower() == preferences["property_type"].lower():
            reasons.append(f"matches property type: {listing['property_type']}")

    if listing.get("verified"):
        reasons.append("owner verified")

    if listing.get("rating", 0) >= 4.0:
        reasons.append(f"high rating: {listing['rating']}/5")

    return reasons
