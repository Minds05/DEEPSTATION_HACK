"""
Firebase Firestore service for housing data operations.
Handles listings, schedules, and interaction storage.
"""
import os
import json
from typing import Optional, List, Dict, Any
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import AsyncClient
import asyncio


# ─── Initialization ──────────────────────────────────────────
_db: Optional[Any] = None
_FALLBACK_PATH = Path(__file__).parent.parent / "data" / "housing.json"


def _init_firebase() -> Any:
    """Initialize Firebase Admin SDK (idempotent)."""
    global _db
    if _db is not None:
        return _db

    # Check if already initialized
    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        if cred_path and Path(cred_path).exists():
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            # Use Application Default Credentials (for Cloud Run)
            firebase_admin.initialize_app()

    _db = firestore.client()
    return _db


def get_db() -> Any:
    """Get initialized Firestore client."""
    return _init_firebase()


def _load_fallback_data() -> List[Dict]:
    """Load housing.json as fallback when Firestore unavailable."""
    try:
        with open(_FALLBACK_PATH, "r") as f:
            data = json.load(f)
            return data.get("listings", [])
    except Exception:
        return []


# ─── Listing Operations ──────────────────────────────────────
async def get_listings(
    budget: Optional[int] = None,
    location: Optional[str] = None,
    property_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    """
    Query housing listings from Firestore with filters.
    Falls back to housing.json if Firestore fails.
    Returns paginated results.
    """
    try:
        db = get_db()
        query = db.collection("housing_listings")

        if property_type:
            query = query.where("property_type", "==", property_type)
        if location:
            query = query.where("location", "==", location)

        # Execute query in thread pool (Firestore sync client)
        loop = asyncio.get_event_loop()
        docs = await loop.run_in_executor(None, lambda: list(query.stream()))

        listings = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            if budget and data.get("rent", 0) > budget:
                continue
            listings.append(data)

        total = len(listings)
        start = (page - 1) * page_size
        paginated = listings[start: start + page_size]

        return {"results": paginated, "total": total, "source": "firestore"}

    except Exception as e:
        # Firestore unavailable — use fallback dataset
        return await _get_listings_fallback(budget, location, property_type, page, page_size)


async def _get_listings_fallback(
    budget, location, property_type, page, page_size
) -> Dict[str, Any]:
    """Filter and paginate from local housing.json fallback."""
    all_listings = _load_fallback_data()
    filtered = []

    for listing in all_listings:
        if budget and listing.get("rent", 0) > budget:
            continue
        if location and location.lower() not in listing.get("location", "").lower():
            continue
        if property_type and listing.get("property_type", "").lower() != property_type.lower():
            continue
        filtered.append(listing)

    total = len(filtered)
    start = (page - 1) * page_size
    paginated = filtered[start: start + page_size]
    return {"results": paginated, "total": total, "source": "fallback"}


async def get_listing_by_id(listing_id: str) -> Optional[Dict]:
    """Fetch a single listing by ID from Firestore or fallback."""
    try:
        db = get_db()
        loop = asyncio.get_event_loop()
        doc = await loop.run_in_executor(
            None, lambda: db.collection("housing_listings").document(listing_id).get()
        )
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
    except Exception:
        pass

    # Fallback search
    for listing in _load_fallback_data():
        if listing.get("id") == listing_id:
            return listing
    return None


# ─── Schedule Operations ─────────────────────────────────────
async def check_slot_conflict(property_id: str, slot: str) -> bool:
    """Returns True if a visit is already booked at this slot."""
    try:
        db = get_db()
        loop = asyncio.get_event_loop()
        docs = await loop.run_in_executor(
            None,
            lambda: list(
                db.collection("schedules")
                .where("property_id", "==", property_id)
                .where("slot", "==", slot)
                .where("status", "==", "confirmed")
                .stream()
            ),
        )
        return len(docs) > 0
    except Exception:
        return False


async def create_schedule(schedule_data: Dict) -> str:
    """Create a visit schedule record in Firestore. Returns document ID."""
    try:
        db = get_db()
        loop = asyncio.get_event_loop()
        doc_ref = await loop.run_in_executor(
            None, lambda: db.collection("schedules").add(schedule_data)
        )
        # doc_ref is a tuple (timestamp, DocumentReference)
        return doc_ref[1].id
    except Exception as e:
        # Return a mock ID in dev/fallback mode
        import uuid
        return f"v{str(uuid.uuid4())[:8]}"


# ─── Interaction Logging ─────────────────────────────────────
async def log_interaction(interaction_data: Dict) -> None:
    """Log a user-agent interaction to Firestore for analytics."""
    try:
        db = get_db()
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: db.collection("interactions").add(interaction_data)
        )
    except Exception:
        pass  # Non-critical, don't fail the request


# ─── Admin Queue ─────────────────────────────────────────────
async def add_to_admin_queue(queue_data: Dict) -> str:
    """Add an item to the admin verification queue."""
    try:
        db = get_db()
        loop = asyncio.get_event_loop()
        doc_ref = await loop.run_in_executor(
            None, lambda: db.collection("admin_queue").add(queue_data)
        )
        return doc_ref[1].id
    except Exception:
        import uuid
        return f"q{str(uuid.uuid4())[:8]}"


async def update_admin_queue_item(item_id: str, update_data: Dict) -> None:
    """Update an admin queue item (e.g., mark as completed)."""
    try:
        db = get_db()
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: db.collection("admin_queue").document(item_id).update(update_data),
        )
    except Exception:
        pass
