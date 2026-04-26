import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

# Load .env from repo root (2 levels up from apps/api)
_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_env_path)

from .routes.analytics import router as analytics_router  # noqa: E402
from .routes.engagement import router as engagement_router  # noqa: E402
from .routes.nudges import router as nudges_router  # noqa: E402
from .websocket_call import router as websocket_router  # noqa: E402


def _cors_origins() -> list[str]:
    raw = os.environ.get("CORS_ORIGINS")
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return ["http://localhost:3000", "http://127.0.0.1:3000"]


app = FastAPI(
    title="SAARTHI API",
    version="0.1.0",
    description="Self-Adaptive AI for Responsible Tele-conversational Human Interaction in BFSI",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(websocket_router)
app.include_router(analytics_router, prefix="/api")
app.include_router(engagement_router, prefix="/api")
app.include_router(nudges_router, prefix="/api")


@app.on_event("startup")
async def ensure_dev_tables() -> None:
    """Create local dev tables when Alembic has not been run yet."""
    try:
        from .db import create_all_tables

        await create_all_tables()
    except Exception as exc:
        print(f"[Startup] Skipping automatic table creation: {exc}")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> str:
    from .metrics import get_collector
    return get_collector().prometheus_format()
