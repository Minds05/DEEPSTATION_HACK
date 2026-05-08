"""
Twilio WhatsApp notification service.
Sends visit reminders and housing alerts via WhatsApp.
"""
import os
from typing import Optional, Dict
from twilio.rest import Client


def _get_twilio_client() -> Client:
    """Initialize Twilio client from environment variables."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    if not account_sid or not auth_token:
        raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set")
    return Client(account_sid, auth_token)


async def send_whatsapp_message(to_number: str, message: str) -> Dict:
    """
    Send a WhatsApp message via Twilio.
    to_number: recipient phone number with country code (e.g. +919876543210)
    """
    from_number = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    # Normalize the number to WhatsApp format
    if not to_number.startswith("whatsapp:"):
        to_number = f"whatsapp:{to_number}"

    try:
        client = _get_twilio_client()
        msg = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number,
        )
        return {"sid": msg.sid, "status": msg.status, "sent": True}
    except Exception as e:
        return {"sent": False, "error": str(e)}


async def send_visit_reminder(
    phone: str, property_title: str, slot: str, visit_id: str
) -> Dict:
    """Send a visit confirmation and reminder via WhatsApp."""
    message = (
        f"✅ Visit Confirmed!\n\n"
        f"Property: {property_title}\n"
        f"Date & Time: {slot}\n"
        f"Visit ID: {visit_id}\n\n"
        f"Please arrive 5 minutes early. "
        f"Reply CANCEL to cancel this visit."
    )
    return await send_whatsapp_message(phone, message)


async def send_housing_alert(phone: str, listing_title: str, rent: int, location: str) -> Dict:
    """Send an alert when a matching listing is found."""
    message = (
        f"🏠 New Listing Alert!\n\n"
        f"Property: {listing_title}\n"
        f"Rent: ₹{rent}/month\n"
        f"Location: {location}\n\n"
        f"Reply VIEW to see details."
    )
    return await send_whatsapp_message(phone, message)



