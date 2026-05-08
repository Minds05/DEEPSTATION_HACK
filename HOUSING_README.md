# Housing Sub-Orchestrator System
## Community Resource Hub — Housing Module

A production-ready, multi-agent AI system for housing discovery, recommendation, negotiation, and visit scheduling.

---

## Architecture

```
Frontend (React + TailwindCSS)
        ↓ Axios
Backend (FastAPI)
        ↓
Housing Sub-Orchestrator
        ↓ Intent Classification (Gemini)
        ├── Preference Agent  → Extracts structured preferences
        ├── Search Agent      → Queries Firestore / housing.json
        ├── Recommendation    → Ranks listings (scoring + Gemini)
        ├── Negotiation       → Generates negotiation messages
        └── Scheduling        → Books visits + Twilio reminders

Admin APIs (independent, not in live routing):
        ├── Verification Agent    → Aadhaar/PAN/face verification
        ├── Fraud Detection Agent → Image hash + pricing anomaly
        └── Agreement Analysis    → PDF parsing + legal reasoning
```

---

## Quick Start

### 1. Python Virtual Environment

```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

### 4. Start Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API Docs: http://localhost:8000/docs

### 5. Frontend Setup

```bash
cd frontend
npm install
```

### 6. Start Frontend

```bash
cd frontend
npm run dev
```

Frontend: http://localhost:5173

---

## Environment Variables

See `backend/.env.example` for all required variables:

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini 2.0 Flash API key |
| `FIREBASE_SERVICE_ACCOUNT_PATH` | Path to Firebase service account JSON |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token |
| `TWILIO_WHATSAPP_FROM` | Twilio WhatsApp sender number |

---

## API Reference

### User-Side Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/housing/chat` | Conversational orchestrator entry |
| POST | `/api/housing/search` | Structured search with filters |
| POST | `/api/housing/recommend` | Rank listings by preferences |
| POST | `/api/housing/negotiate` | Generate negotiation message |
| POST | `/api/housing/schedule` | Book a property visit |

### Admin-Side Endpoints (Independent)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/admin/verify-owner` | Owner document verification |
| POST | `/api/admin/fraud-check` | Fraud detection for listings |
| POST | `/api/admin/analyze-agreement` | Rental agreement analysis |

---

## Chat Example

```json
POST /api/housing/chat
{
  "query": "Need quiet PG near metro under 8000",
  "user_id": "u10"
}
```

Response:
```json
{
  "task": "recommend",
  "response": {
    "preferences": { "budget": 8000, "location": "Whitefield", "property_type": "PG" },
    "search": { "results": [...], "total": 3 },
    "recommendations": { "recommendations": [{ "listing_id": "h01", "score": 88 }] }
  }
}
```

---

## Firebase Firestore Collections

| Collection | Purpose |
|---|---|
| `housing_listings` | Property listings |
| `schedules` | Visit bookings |
| `interactions` | Agent interaction logs |
| `admin_queue` | Admin verification queue |

---

## Fallback Mode

If Firebase is not configured, the system automatically falls back to `backend/app/data/housing.json` for listings. All other features (Gemini, Twilio) still require valid API keys.

---

## Tech Stack

- **Backend**: FastAPI, Uvicorn, Firebase Admin SDK, Google Generative AI (Gemini 2.0 Flash)
- **Frontend**: React 18, Vite, TailwindCSS, Axios, Lucide React
- **Database**: Firebase Firestore
- **Notifications**: Twilio WhatsApp API
- **AI**: Gemini 2.0 Flash (temperature=0.2, JSON mode)

---

## Deployment

### Backend — Google Cloud Run

```bash
gcloud run deploy housing-orchestrator \
  --source backend/ \
  --region asia-south1 \
  --set-env-vars GEMINI_API_KEY=xxx
```

### Frontend — Firebase Hosting

```bash
cd frontend && npm run build
firebase deploy --only hosting
```
