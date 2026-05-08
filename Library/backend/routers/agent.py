from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_db
import google.generativeai as genai
import os
import json
from sentence_transformers import SentenceTransformer
import numpy as np

try:
    print("Loading SentenceTransformer model...")
    model_st = SentenceTransformer('all-MiniLM-L6-v2')
    print("Model loaded successfully.")
except Exception as e:
    print(f"Failed to load SentenceTransformer: {e}")
    model_st = None

def cosine_similarity(a, b):
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

router = APIRouter()

class QueryRequest(BaseModel):
    user_query: str
    user_id: str

# Ensure API key is configured (assumes GEMINI_API_KEY in env)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

@router.post("/query")
async def process_agent_query(request: QueryRequest):
    """
    Agent Query Endpoint
    Accepts user_query and user_id.
    Logic: If Syllabus/JD, keyword search Firestore metadata.
    Intelligence: Send Syllabus + top 15 book metadata to Gemini.
    """
    db = get_db()
    
    # 1. Fetch metadata from Firestore
    inventory_ref = db.collection('library_inventory')
    docs = inventory_ref.stream()
    
    books_metadata = []
    for doc in docs:
        books_metadata.append(doc.to_dict())
        
    if not books_metadata:
        raise HTTPException(status_code=404, detail="No books found in inventory.")
        
    if model_st:
        query_embedding = model_st.encode(request.user_query)
        for book in books_metadata:
            search_text = f"{book.get('title', '')} {book.get('genre', '')} {book.get('author', '')}"
            book_embedding = model_st.encode(search_text)
            sim_score = cosine_similarity(query_embedding, book_embedding)
            book['_relevance'] = sim_score + (book.get('popularity_score', 0) * 0.01)
    else:
        # Fallback to naive keyword search if model didn't load
        query_words = set(request.user_query.lower().split())
        for book in books_metadata:
            score = 0
            search_text = (str(book.get('title', '')) + " " + str(book.get('genre', '')) + " " + str(book.get('author', ''))).lower()
            for word in query_words:
                if len(word) > 3 and word in search_text:
                    score += 1
            book['_relevance'] = score + (book.get('popularity_score', 0) * 0.1)

    # Sort by relevance and take top 10
    books_metadata.sort(key=lambda x: x.get('_relevance', 0), reverse=True)
    top_10_books = books_metadata[:10]
    
    # Remove internal _relevance key
    for b in top_10_books:
        b.pop('_relevance', None)
        
    books_json = json.dumps(top_10_books, indent=2)

    # 2. Gemini System Prompt
    system_instruction = '''You are an expert Academic Advisor and a Sentinel Orchestrator. 
Your task is to analyze a given syllabus or Job Description (JD) and recommend the 3 most relevant books from the provided catalog.
If the user's query is out of bounds for a Library (e.g., they ask for physical lab equipment, project supervision, or server space), you MUST initiate a handoff.

CRITICAL INSTRUCTIONS:
1. DO NOT summarize the syllabus or JD.
2. Identify the core technical modules or themes required.
3. Select EXACTLY 3 books from the provided catalog that best match the technical modules.
4. If a perfect match does not exist in the catalog, select the closest alternative. DO NOT hallucinate ISBNs.
5. If the query requires Lab Equipment, return a JSON with a handoff action to "Lab_Agent".
6. Your output MUST be strictly a valid JSON object.

Valid Schema for standard response:
{
  "message": "Based on your syllabus, you will be diving deep into system design. I recommend these texts.",
  "book_ids": ["978-0131103627", "978-1098120501", "978-0134685991"]
}

Valid Schema for handoff response:
{
  "action": "HANDOFF",
  "target": "Lab_Agent",
  "message": "Redirecting you to the Lab Resource Agent for your equipment needs..."
}'''
    
    prompt = f"""
    User Query (Syllabus/JD):
    {request.user_query}
    
    Available Books Metadata Catalog:
    {books_json}
    """
    
    try:
        model = genai.GenerativeModel(
            model_name="gemini-flash-latest",
            system_instruction=system_instruction,
            generation_config={"response_mime_type": "application/json"}
        )
        response = model.generate_content(prompt)
        
        res_text = response.text.strip()
        # Ensure it parses as JSON properly
        parsed_response = json.loads(res_text)
        return parsed_response
        
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        raise HTTPException(status_code=500, detail=str(e))
