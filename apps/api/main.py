from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

from websocket_call import router as websocket_router

# Load .env from repo root (2 levels up from apps/api)
_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_env_path)

app = FastAPI(
    title="SAARTHI API",
    version="0.1.0",
    description="Self-Adaptive AI for Responsible Tele-conversational Human Interaction in BFSI",
)
app.include_router(websocket_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> str:
    # Prometheus-compatible metrics endpoint — populated in Phase 1
    return "# SAARTHI metrics\n# p50/p95 per hop added in Phase 1\n"
