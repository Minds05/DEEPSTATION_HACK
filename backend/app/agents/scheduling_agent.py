"""
Scheduling Agent — USER SIDE
Handles property visit scheduling with collision detection and Twilio reminders.
Writes to Firestore and sends WhatsApp notifications.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from app.services.firestore_service import check_slot_conflict, create_schedule, get_listing_by_id
from app.services.twilio_service import send_visit_reminder


async def run(
    property_id: str,
    user_id: str,
    slot: str,
    user_phone: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Schedule a property visit.

    Input:
        property_id: Listing ID to visit
        user_id: Authenticated user's ID
        slot: ISO 8601 datetime (e.g. "2026-05-09T17:00:00")
        user_phone: Optional phone for Twilio reminder
        notes: Optional visit notes

    Output:
        {
            "status": "scheduled" | "conflict",
            "visit_id": str,
            "property_id": str,
            "user_id": str,
            "slot": str,
            "notification_sent": bool
        }
    """
    # Step 1: Validate slot datetime format
    try:
        datetime.fromisoformat(slot)
    except ValueError:
        return {
            "status": "error",
            "error": f"Invalid slot format: {slot}. Use ISO 8601.",
            "visit_id": "",
            "property_id": property_id,
            "user_id": user_id,
            "slot": slot,
            "notification_sent": False,
        }

    # Step 2: Check for slot conflicts
    conflict = await check_slot_conflict(property_id, slot)
    if conflict:
        return {
            "status": "conflict",
            "error": "This time slot is already booked. Please choose a different time.",
            "visit_id": "",
            "property_id": property_id,
            "user_id": user_id,
            "slot": slot,
            "notification_sent": False,
        }

    # Step 3: Create schedule record in Firestore
    visit_id = f"v{str(uuid.uuid4())[:8]}"
    schedule_data = {
        "visit_id": visit_id,
        "property_id": property_id,
        "user_id": user_id,
        "slot": slot,
        "status": "confirmed",
        "notes": notes,
        "created_at": datetime.utcnow().isoformat(),
    }
    firestore_id = await create_schedule(schedule_data)

    # Step 4: Fetch listing title for notification
    notification_sent = False
    if user_phone:
        listing = await get_listing_by_id(property_id)
        property_title = listing.get("title", property_id) if listing else property_id
        result = await send_visit_reminder(user_phone, property_title, slot, visit_id)
        notification_sent = result.get("sent", False)

    return {
        "status": "scheduled",
        "visit_id": firestore_id or visit_id,
        "property_id": property_id,
        "user_id": user_id,
        "slot": slot,
        "notification_sent": notification_sent,
    }
