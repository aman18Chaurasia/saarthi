"""Analytics API endpoints."""
from datetime import datetime
from typing import Any
from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/calls")
async def list_calls(
    product: str | None = None,
    status: str | None = None,
    outcome: str | None = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
) -> dict[str, Any]:
    """List calls with filtering and pagination."""
    # TODO: Implement database query when DB connected
    return {
        "calls": [],
        "total": 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/analytics/summary")
async def analytics_summary(
    product: str | None = None,
) -> dict[str, Any]:
    """Aggregated analytics summary."""
    return {
        "total_calls": 0,
        "qualified_count": 0,
        "qualified_rate": 0.0,
        "avg_duration_s": 0.0,
        "avg_turn_count": 0.0,
        "p50_latency": 0.0,
        "p95_latency": 0.0,
    }


@router.get("/analytics/by_product")
async def analytics_by_product() -> list[dict[str, Any]]:
    """Per-product analytics breakdown."""
    products = [
        "personal_loan", "home_loan", "education_loan", "gold_loan", "credit_card",
        "unsecured_loan", "lap_secured", "commercial_vehicle", "four_wheeler", "msme_business"
    ]
    return [
        {
            "product": p,
            "call_count": 0,
            "qualified_rate": 0.0,
            "avg_duration": 0.0
        }
        for p in products
    ]
