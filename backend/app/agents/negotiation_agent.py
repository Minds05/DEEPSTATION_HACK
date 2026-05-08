"""
Negotiation Agent — USER SIDE
Generates professional, concise rent negotiation messages.
Returns strict JSON with strategy and message.
"""
from typing import Dict, Any, Optional
from app.services.gemini_service import generate_json
from app.utils.prompts import NEGOTIATION_MESSAGE_PROMPT


async def run(
    current_rent: int,
    target_rent: int,
    property_type: str = "flat",
    tenant_profile: str = "working professional",
    language: str = "English",
) -> Dict[str, Any]:
    """
    Generate a rent negotiation message.

    Input:
        current_rent: Landlord's asking price
        target_rent: Tenant's desired rent
        property_type: Type of property (PG, flat, etc.)
        tenant_profile: Brief profile of the tenant
        language: Language for the message

    Output:
        {
            "message": str,
            "strategy": str,
            "fallback_rent": int,
            "key_points": [...]
        }
    """
    # Validate: target must be less than current for negotiation
    if target_rent >= current_rent:
        return {
            "message": f"The listed rent of ₹{current_rent} is already within your budget.",
            "strategy": "no_negotiation_needed",
            "fallback_rent": current_rent,
            "key_points": ["rent is within budget"],
        }
        
    savings = current_rent - target_rent
    savings_pct = round((savings / current_rent) * 100)
    
    # Enforce strict 10-20% discount rule requested by user
    if savings_pct < 10 or savings_pct > 20:
        raise ValueError("Disagree: The owner is only willing to consider a reasonable discount between 10% and 20%. Please adjust your target amount.")

    prompt = NEGOTIATION_MESSAGE_PROMPT.format(
        current_rent=current_rent,
        target_rent=target_rent,
        property_type=property_type,
        tenant_profile=tenant_profile,
        language=language,
    )

    result = await generate_json(prompt)

    return {
        "message": result.get("message", ""),
        "strategy": result.get("strategy", ""),
        "fallback_rent": result.get("fallback_rent", int((current_rent + target_rent) / 2)),
        "key_points": result.get("key_points", []),
    }
