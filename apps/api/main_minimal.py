"""Minimal FastAPI for Cloud Run deployment - health check + Chirp demo"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SAARTHI API (Minimal)",
    version="0.1.0",
    description="Hackathon demo with Chirp-3 integration",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok", "chirp_configured": bool(os.getenv("ASR_PROVIDER") == "chirp")}


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint"""
    return {
        "message": "SAARTHI API - Hackathon Demo",
        "asr_provider": os.getenv("ASR_PROVIDER", "none"),
        "llm_provider": os.getenv("LLM_PROVIDER", "none"),
        "project": "saarthi-hackathon",
    }


@app.get("/config")
async def config() -> dict[str, str]:
    """Show configuration (for demo)"""
    return {
        "asr_provider": os.getenv("ASR_PROVIDER", "not set"),
        "llm_provider": os.getenv("LLM_PROVIDER", "not set"),
        "tts_provider": os.getenv("TTS_PROVIDER", "not set"),
        "google_speech_location": os.getenv("GOOGLE_SPEECH_LOCATION", "not set"),
        "groq_model": os.getenv("GROQ_MODEL", "not set"),
    }
