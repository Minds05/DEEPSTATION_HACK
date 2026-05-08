# C-IAW — Cloud Run Source Deployment Guide
# Run these commands from the project root: career-agent/

# ──────────────────────────────────────────────────────────────
# PREREQUISITES
# ──────────────────────────────────────────────────────────────
# 1. Install Google Cloud CLI: https://cloud.google.com/sdk/docs/install
# 2. Authenticate: gcloud auth login
# 3. Set your project: gcloud config set project YOUR_PROJECT_ID
# 4. Enable APIs:
#    gcloud services enable run.googleapis.com
#    gcloud services enable cloudbuild.googleapis.com

# ──────────────────────────────────────────────────────────────
# STEP 1 — Create a Secret for your service account JSON
# ──────────────────────────────────────────────────────────────
# gcloud secrets create firebase-sa --data-file=./backend/firebase-service-account.json

# ──────────────────────────────────────────────────────────────
# STEP 2 — Deploy backend to Cloud Run (source-based, no Docker)
# ──────────────────────────────────────────────────────────────
# cd backend
# gcloud run deploy ciaw-backend \
#   --source . \
#   --region us-central1 \
#   --platform managed \
#   --allow-unauthenticated \
#   --set-env-vars "ENV=production,USER_ID=local_user,MATCH_THRESHOLD=92" \
#   --set-secrets "GEMINI_API_KEY=gemini-api-key:latest,FIREBASE_STORAGE_BUCKET=firebase-storage-bucket:latest" \
#   --memory 1Gi \
#   --cpu 1 \
#   --concurrency 10 \
#   --timeout 300

# After deploy, note the Service URL (e.g. https://ciaw-backend-xxx-uc.a.run.app)
# Set it in frontend/.env: VITE_API_BASE_URL=https://ciaw-backend-xxx-uc.a.run.app

# ──────────────────────────────────────────────────────────────
# STEP 3 — Deploy frontend to Netlify
# ──────────────────────────────────────────────────────────────
# cd ../frontend
# npm run build
# npx netlify-cli deploy --prod --dir=dist

# Or connect your GitHub repo in the Netlify dashboard and set:
#   Build command: npm run build
#   Publish directory: dist
#   Environment variables: all VITE_* from frontend/.env

# ──────────────────────────────────────────────────────────────
# STEP 4 — Playwright on Cloud Run
# ──────────────────────────────────────────────────────────────
# The Procfile runs: playwright install chromium on first startup (production mode).
# Ensure --memory 1Gi or higher to handle headless browser.
