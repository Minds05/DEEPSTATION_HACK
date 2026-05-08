from fastapi import APIRouter
from database import get_db
from datetime import datetime, timezone

router = APIRouter()

@router.post("/check_rentals/{user_id}")
async def check_user_rentals(user_id: str):
    """
    Logistics Engine:
    Implement an internal function to check active_rentals. 
    If today > due_date, it must trigger a notification update in Firestore.
    """
    db = get_db()
    user_ref = db.collection('user_states').document(user_id)
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        return {"status": "User not found"}
        
    user_data = user_doc.to_dict()
    active_rentals = user_data.get("active_rentals", [])
    notifications = user_data.get("notifications", [])
    
    today_iso = datetime.now(timezone.utc).isoformat()
    
    updated = False
    for rental in active_rentals:
        if rental.get('status') == 'rented':
            due_date = rental.get('due_date')
            if due_date and today_iso > due_date:
                # Late! Trigger notification
                msg = f"Overdue Alert: Your rental for ISBN {rental.get('isbn')} is late!"
                
                # Simple deduplication
                already_notified = any(
                    n.get('type') == 'overdue' and str(rental.get('isbn')) in n.get('msg') 
                    for n in notifications
                )
                
                if not already_notified:
                    notifications.append({
                        "msg": msg,
                        "timestamp": today_iso,
                        "type": "overdue"
                    })
                    updated = True

    if updated:
        user_ref.update({"notifications": notifications})
        return {"status": "Notifications updated", "new_notifications": True}
        
    return {"status": "No new notifications", "new_notifications": False}
