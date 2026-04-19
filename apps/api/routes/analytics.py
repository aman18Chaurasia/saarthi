"""Dashboard analytics API endpoints."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from db import get_session
from models.call import Call

router = APIRouter()

PRODUCTS = [
    "personal_loan",
    "home_loan",
    "education_loan",
    "gold_loan",
    "credit_card",
    "unsecured_loan",
    "lap_secured",
    "commercial_vehicle",
    "four_wheeler",
    "msme_business",
]


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = round((len(ordered) - 1) * (percentile / 100))
    return round(ordered[index], 2)


def _call_to_dict(call: Call) -> dict[str, Any]:
    return {
        "call_id": call.call_id,
        "customer_id": call.customer_id,
        "product": call.product,
        "agent_name": call.agent_name,
        "lender_name": call.lender_name,
        "customer_name_redacted": call.customer_name_redacted,
        "status": call.status,
        "outcome": call.outcome,
        "started_at": call.started_at.isoformat(),
        "ended_at": call.ended_at.isoformat() if call.ended_at else None,
        "duration_s": call.duration_s,
        "turn_count": call.turn_count,
        "error_count": call.error_count,
        "audio_failed": call.audio_failed,
    }


async def _load_calls(session: AsyncSession) -> list[Call]:
    result = await session.exec(select(Call))
    return list(result.all())


def _filter_calls(
    calls: list[Call],
    *,
    product: str | None = None,
    status: str | None = None,
    outcome: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[Call]:
    filtered = calls
    if product:
        filtered = [call for call in filtered if call.product == product]
    if status:
        filtered = [call for call in filtered if call.status == status]
    if outcome:
        filtered = [call for call in filtered if call.outcome == outcome]
    if date_from:
        filtered = [call for call in filtered if call.started_at >= date_from.replace(tzinfo=None)]
    if date_to:
        filtered = [call for call in filtered if call.started_at <= date_to.replace(tzinfo=None)]
    return filtered


def _summary(calls: list[Call]) -> dict[str, Any]:
    total = len(calls)
    qualified = sum(1 for call in calls if call.outcome == "qualified")
    durations = [call.duration_s for call in calls if call.duration_s is not None]
    turns = [call.turn_count for call in calls]
    e2e_p50_values = [
        float(call.latency_stats["e2e_p50"])
        for call in calls
        if isinstance(call.latency_stats.get("e2e_p50"), (int, float))
    ]
    e2e_p95_values = [
        float(call.latency_stats["e2e_p95"])
        for call in calls
        if isinstance(call.latency_stats.get("e2e_p95"), (int, float))
    ]

    return {
        "total_calls": total,
        "qualified_count": qualified,
        "qualified_rate": round((qualified / total) * 100, 2) if total else 0.0,
        "avg_duration_s": round(sum(durations) / len(durations), 2) if durations else 0.0,
        "avg_turn_count": round(sum(turns) / len(turns), 2) if turns else 0.0,
        "p50_latency": _percentile(e2e_p50_values, 50),
        "p95_latency": _percentile(e2e_p95_values, 95),
    }


@router.get("/calls")
async def list_calls(
    product: str | None = None,
    status: str | None = None,
    outcome: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    calls = _filter_calls(
        await _load_calls(session),
        product=product,
        status=status,
        outcome=outcome,
        date_from=date_from,
        date_to=date_to,
    )
    calls.sort(key=lambda call: call.started_at, reverse=True)
    page = calls[offset : offset + limit]

    return {
        "calls": [_call_to_dict(call) for call in page],
        "total": len(calls),
        "limit": limit,
        "offset": offset,
    }


@router.get("/analytics/summary")
async def analytics_summary(
    product: str | None = None,
    status: str | None = None,
    outcome: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    calls = _filter_calls(
        await _load_calls(session),
        product=product,
        status=status,
        outcome=outcome,
        date_from=date_from,
        date_to=date_to,
    )
    return _summary(calls)


@router.get("/analytics/by_product")
async def analytics_by_product(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    grouped: dict[str, list[Call]] = defaultdict(list)
    for call in await _load_calls(session):
        grouped[call.product].append(call)

    return [
        {
            "product": product,
            "call_count": len(grouped[product]),
            "qualified_rate": _summary(grouped[product])["qualified_rate"],
            "avg_duration": _summary(grouped[product])["avg_duration_s"],
        }
        for product in PRODUCTS
    ]
