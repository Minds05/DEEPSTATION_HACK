import pandas as pd
import random
from database import get_db
import argparse

def run_kaggle_seeder(limit=500):
    print("Fetching Kaggle (Goodreads-10k) dataset...")
    url = "https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master/books.csv"
    
    # Read CSV
    df = pd.read_csv(url)
    
    # Clean data: Remove rows where ISBN is null or missing
    df = df.dropna(subset=['isbn', 'title', 'authors', 'average_rating'])
    
    # Sample top books to avoid free tier quota limits (limit = 500)
    df = df.head(limit)
    
    db = get_db()
    batch = db.batch()
    inventory_ref = db.collection('library_inventory')
    
    genres = ["Computer Science", "Software Engineering", "Fiction", "Fantasy", "Science Fiction", "Biography", "History", "Business"]
    
    count = 0
    for _, row in df.iterrows():
        isbn = str(row['isbn']).strip()
        if not isbn:
            continue
            
        # Mock some fields since they don't exist in the goodbooks dataset
        buy_price = round(random.uniform(10.0, 80.0), 2)
        rent_price = round(buy_price * 0.10, 2)
        rating = float(row['average_rating'])
        popularity_score = min(10.0, round((rating * 2.0), 1))
        
        # Assign random genres to give Gemini something to filter on
        genre = random.choice(genres)
        
        doc_ref = inventory_ref.document(isbn)
        
        book_data = {
            'isbn': isbn,
            'title': str(row['title']),
            'author': str(row['authors']),
            'genre': genre,
            'popularity_score': popularity_score,
            'buy_price': buy_price,
            'rent_price': rent_price,
            'status': 'available',
            'rating': rating
        }
        
        batch.set(doc_ref, book_data)
        count += 1
        
        # Firestore batches max out at 500 operations
        if count % 400 == 0:
            batch.commit()
            batch = db.batch()
            
    if count % 400 != 0:
        batch.commit()
        
    print(f"Successfully seeded {count} books from Kaggle dataset into 'library_inventory'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Seed Firestore from Kaggle CSV.')
    parser.add_argument('--limit', type=int, default=500, help='Number of books to import')
    args = parser.parse_args()
    
    run_kaggle_seeder(args.limit)
