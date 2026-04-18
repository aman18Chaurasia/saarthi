from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI(
    title="SAARTHI API",
    version="0.1.0",
    description="Self-Adaptive AI for Responsible Tele-conversational Human Interaction in BFSI",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> str:
    # Prometheus-compatible metrics endpoint — populated in Phase 1
    return "# SAARTHI metrics\n# p50/p95 per hop added in Phase 1\n"
