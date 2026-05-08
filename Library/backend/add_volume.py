import random
from database import get_db

def run():
    db = get_db()
    inventory_ref = db.collection('library_inventory')
    docs = inventory_ref.stream()

    batch = db.batch()
    count = 0
    for doc in docs:
        # 20% chance of out of stock (volume=0), 80% chance of 1-10 volume
        vol = 0 if random.random() < 0.2 else random.randint(1, 10)
        batch.update(doc.reference, {'volume': vol})
        count += 1
        
        # Firestore batches max out at 500 operations
        if count % 400 == 0:
            batch.commit()
            batch = db.batch()

    if count % 400 != 0:
        batch.commit()

    print(f"Successfully added 'volume' field to {count} books.")

if __name__ == "__main__":
    run()
