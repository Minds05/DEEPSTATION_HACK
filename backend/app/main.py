"""
C-IAW FastAPI Application Entry Point
"""
import subprocess
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import resume, agent, jobs, applications
from app.db.firestore_client import init_firestore


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # ── Firestore init ────────────────────────────────────────
    init_firestore()

    # ── Playwright Chromium install (Cloud Run, production only) ─
    if settings.is_production:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True
        )

    yield
    # ── Shutdown cleanup ──────────────────────────────────────
    from app.browser.browser_controller import close_browser
    await close_browser()


app = FastAPI(
    title="C-IAW Career Intelligence API",
    description="Autonomous job lifecycle agent: parse → hunt → score → apply.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────
app.include_router(resume.router,       prefix="/resume",       tags=["Resume"])
app.include_router(agent.router,        prefix="/agent",        tags=["Agent"])
app.include_router(jobs.router,         prefix="/jobs",         tags=["Jobs"])
app.include_router(applications.router, prefix="/applications", tags=["Applications"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "agent": "C-IAW",
        "env": settings.env,
        "threshold": settings.match_threshold,
    }
