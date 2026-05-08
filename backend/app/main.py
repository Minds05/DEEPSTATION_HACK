"""
FastAPI main application entry point.
Housing Sub-Orchestrator System — Community Resource Hub Platform.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from app.routes.housing import router as housing_router
from app.routes.admin_housing import router as admin_housing_router

app = FastAPI(
    title="Housing Sub-Orchestrator API",
    description="Community Resource Hub — Housing Module. User-facing and admin-side housing agents.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ─────────────────────────────────────────────────────
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ───────────────────────────────────────────────────
# USER SIDE: fully integrated into live orchestration
app.include_router(housing_router)

# ADMIN SIDE: independent API, NOT connected to user routing
app.include_router(admin_housing_router)


@app.get("/")
async def root():
    return {
        "service": "Housing Sub-Orchestrator",
        "version": "1.0.0",
        "status": "running",
        "user_routes": [
            "POST /api/housing/chat",
            "POST /api/housing/search",
            "POST /api/housing/recommend",
            "POST /api/housing/negotiate",
            "POST /api/housing/schedule",
        ],
        "admin_routes": [
            "POST /api/admin/verify-owner",
            "POST /api/admin/fraud-check",
            "POST /api/admin/analyze-agreement",
        ],
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "housing-orchestrator"}
