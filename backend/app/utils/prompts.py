# ============================================================
# REUSABLE PROMPTS FOR ALL HOUSING AGENTS
# All prompts enforce strict JSON output - no decorative text
# ============================================================

PREFERENCE_EXTRACTION_PROMPT = """
You are a housing preference extraction engine.
Extract structured preferences from the user query.
Return ONLY valid JSON. No explanations, no greetings, no markdown.

User query: {query}

Return this exact JSON structure:
{{
  "budget": <integer or null>,
  "location": <string or null>,
  "property_type": <"PG" | "flat" | "apartment" | "room" | "hostel" | null>,
  "bedrooms": <integer or null>,
  "furnishing": <"fully_furnished" | "semi_furnished" | "unfurnished" | null>,
  "occupancy": <"single" | "shared" | "family" | null>,
  "gender_preference": <"male" | "female" | "any" | null>,
  "preferences": [<list of string features mentioned>],
  "nearby_requirements": [<list of nearby places required>],
  "move_in_date": <"YYYY-MM-DD" or null>
}}
"""

RECOMMENDATION_RANKING_PROMPT = """
You are a housing recommendation engine.
Rank the provided listings by relevance to user preferences.
Return ONLY valid JSON. No explanations.

User preferences:
{preferences}

Listings to rank:
{listings}

Return this exact JSON structure:
{{
  "recommendations": [
    {{
      "listing_id": "<id>",
      "score": <integer 0-100>,
      "reasons": [<list of specific match reasons>],
      "concerns": [<list of potential issues>]
    }}
  ]
}}

Rank from highest to lowest score. Be deterministic and precise.
"""

NEGOTIATION_MESSAGE_PROMPT = """
You are a rental negotiation assistant.
Generate a professional, concise negotiation message.
Return ONLY valid JSON. No decorative language.

Current rent: {current_rent}
Target rent: {target_rent}
Property type: {property_type}
Tenant profile: {tenant_profile}
Language: {language}

Return this exact JSON structure:
{{
  "message": "<concise negotiation message>",
  "strategy": "<negotiation strategy used>",
  "fallback_rent": <integer - acceptable middle ground>,
  "key_points": [<list of leverage points used>]
}}
"""

FRAUD_DETECTION_PROMPT = """
You are a rental listing fraud detection engine.
Analyze the listing data for suspicious patterns.
Return ONLY valid JSON. No explanations.

Listing data:
{listing_data}

Return this exact JSON structure:
{{
  "risk_score": <integer 0-100>,
  "risk_level": <"low" | "medium" | "high" | "critical">,
  "flags": [<list of specific fraud indicators detected>],
  "analysis": {{
    "pricing_anomaly": <boolean>,
    "description_quality": <"poor" | "average" | "good">,
    "contact_suspicious": <boolean>,
    "image_concerns": [<list of image-related concerns>]
  }},
  "recommendation": <"approve" | "review" | "reject">
}}
"""

AGREEMENT_ANALYSIS_PROMPT = """
You are a legal document analysis engine for rental agreements.
Analyze the rental agreement text for risks and issues.
Return ONLY valid JSON. No legal advice disclaimers, no markdown.

Agreement text:
{agreement_text}

Return this exact JSON structure:
{{
  "risk_level": <"low" | "medium" | "high">,
  "overall_score": <integer 0-100, higher is safer>,
  "issues": [<list of specific problematic clauses or terms>],
  "positive_clauses": [<list of tenant-friendly clauses>],
  "missing_clauses": [<list of standard clauses that are absent>],
  "deposit_analysis": {{
    "amount_mentioned": <boolean>,
    "refund_conditions_clear": <boolean>,
    "deduction_rules_specified": <boolean>
  }},
  "termination_analysis": {{
    "notice_period_specified": <boolean>,
    "early_exit_penalty_mentioned": <boolean>
  }},
  "recommendation": "<brief actionable recommendation>"
}}
"""

VERIFICATION_PROMPT = """
You are a property owner verification engine.
Analyze the extracted document data and verify consistency.
Return ONLY valid JSON.

Document data:
{document_data}

Return this exact JSON structure:
{{
  "verification_status": <"verified" | "unverified" | "requires_review">,
  "confidence_score": <integer 0-100>,
  "document_checks": {{
    "aadhaar_valid": <boolean>,
    "pan_valid": <boolean>,
    "ownership_proof_consistent": <boolean>,
    "face_match": <boolean or null>
  }},
  "flags": [<list of inconsistencies found>],
  "recommendation": <"approve" | "manual_review" | "reject">
}}
"""

ORCHESTRATOR_CLASSIFICATION_PROMPT = """
You are a housing request classifier for a multi-agent orchestration system.
Classify the user request and extract structured parameters.
Return ONLY valid JSON. No explanations.

User request: {query}
Conversation history: {history}

Return this exact JSON structure:
{{
  "task": <"search" | "recommend" | "negotiate" | "schedule" | "general_query">,
  "confidence": <integer 0-100>,
  "extracted_params": {{
    "location": <string or null>,
    "budget": <integer or null>,
    "property_type": <string or null>,
    "listing_id": <string or null>,
    "slot": <"ISO datetime string" or null>
  }},
  "requires_agents": [<list of agent names needed>],
  "response_required": <boolean>
}}
"""
