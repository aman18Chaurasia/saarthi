from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

from websocket_call import router as websocket_router
from routes.analytics import router as analytics_router

# Load .env from repo root (2 levels up from apps/api)
_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_env_path)

app = FastAPI(
    title="SAARTHI API",
    version="0.1.0",
    description="Self-Adaptive AI for Responsible Tele-conversational Human Interaction in BFSI",
)
app.include_router(websocket_router)
app.include_router(analytics_router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> str:
    from metrics import get_collector
    return get_collector().prometheus_format()
