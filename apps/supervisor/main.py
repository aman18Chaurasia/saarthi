"""Supervisor service for real-time transcription and nudges.

Separate FastAPI app running on port 8001.
Provides WebSocket endpoints for supervisor UI.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .websocket import router as ws_router

# Load .env from repo root
repo_root = Path(__file__).parents[2]
env_path = repo_root / ".env"
load_dotenv(env_path)

app = FastAPI(
    title="SAARTHI Supervisor Service",
    description="Real-time call transcription and contextual nudge generation",
    version="0.1.0",
)

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        os.getenv("NEXT_PUBLIC_URL", "http://localhost:3000"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket routes
app.include_router(ws_router, prefix="/ws/supervisor")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "supervisor"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "apps.supervisor.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
    )
