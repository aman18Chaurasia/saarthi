"""Tests for dashboard analytics routes."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app
from apps.api.models.call import Call
from apps.api.routes.analytics import get_session


class _FakeResult:
    def __init__(self, rows: list[Call]) -> None:
        self._rows = rows

    def all(self) -> list[Call]:
        return self._rows


class _FakeSession:
    def __init__(self, rows: list[Call]) -> None:
        self._rows = rows

    async def exec(self, _statement: Any) -> _FakeResult:
        return _FakeResult(self._rows)


@pytest.fixture()
def calls() -> list[Call]:
    now = datetime.utcnow()
    return [
        _call(
            "call_001",
            product="personal_loan",
            outcome="qualified",
            started_at=now,
            duration_s=100,
            turn_count=5,
            latency=200,
        ),
        _call(
            "call_002",
            product="home_loan",
            outcome="not_qualified",
            started_at=now - timedelta(days=1),
            duration_s=200,
            turn_count=7,
            latency=300,
        ),
        _call(
            "call_003",
            product="personal_loan",
            outcome="dropped",
            started_at=now - timedelta(days=2),
            duration_s=50,
            turn_count=3,
            latency=150,
        ),
    ]


@pytest.fixture()
def override_session(calls: list[Call]) -> None:
    async def _override() -> _FakeSession:
        return _FakeSession(calls)

    app.dependency_overrides[get_session] = _override
    yield
    app.dependency_overrides.pop(get_session, None)


def _call(
    call_id: str,
    *,
    product: str,
    outcome: str,
    started_at: datetime,
    duration_s: float,
    turn_count: int,
    latency: float,
) -> Call:
    return Call(
        call_id=call_id,
        customer_id=f"cust_{call_id}",
        product=product,
        agent_name="Bunty",
        lender_name="Demo Bank",
        customer_name_redacted="<PERSON_REDACTED>",
        status="completed",
        outcome=outcome,
        started_at=started_at,
        ended_at=started_at + timedelta(seconds=duration_s),
        duration_s=duration_s,
        turn_count=turn_count,
        latency_stats={"e2e_p50": latency, "e2e_p95": latency + 50},
        transcript_redacted=[
            {"speaker": "customer", "text": "eligibility kya hai", "node": "qualify", "turn_index": 1},
            {"speaker": "agent", "text": "documents PAN and Aadhaar", "node": "qualify_followup", "turn_index": 2},
        ],
        slots_redacted={"monthly_income_inr": 50000},
    )


@pytest.mark.asyncio
async def test_list_calls_filters_and_orders(override_session: None) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/calls", params={"product": "personal_loan"})

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["total"] == 2
    assert [call["call_id"] for call in payload["calls"]] == ["call_001", "call_003"]


@pytest.mark.asyncio
async def test_analytics_summary_computes_rates_and_latency(override_session: None) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/analytics/summary")

    assert resp.status_code == 200
    assert resp.json() == {
        "total_calls": 3,
        "qualified_count": 1,
        "qualified_rate": 33.33,
        "avg_duration_s": 116.67,
        "avg_turn_count": 5.0,
        "p50_latency": 200.0,
        "p95_latency": 350.0,
        "high_priority_calls": 1,
        "follow_up_queue": 2,
        "handoff_queue": 1,
        "avg_lead_score": 64.67,
        "negative_sentiment_rate": 0.0,
        "top_objections": [
            {"objection": "documents", "count": 3},
            {"objection": "eligibility", "count": 3},
        ],
    }


@pytest.mark.asyncio
async def test_analytics_by_product_includes_all_products(override_session: None) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/analytics/by_product")

    assert resp.status_code == 200
    products = {row["product"]: row for row in resp.json()}
    assert products["personal_loan"]["call_count"] == 2
    assert products["personal_loan"]["qualified_rate"] == 50.0
    assert products["personal_loan"]["avg_lead_score"] > 0
    assert products["home_loan"]["call_count"] == 1
    assert products["credit_card"]["call_count"] == 0


@pytest.mark.asyncio
async def test_call_detail_returns_transcript_and_intelligence(override_session: None) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/calls/call_001")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["call_id"] == "call_001"
    assert payload["transcript_redacted"][0]["text"] == "eligibility kya hai"
    assert payload["intelligence"]["lead_score"] >= 80
    assert "documents" in payload["intelligence"]["objections"]


@pytest.mark.asyncio
async def test_analytics_ops_returns_follow_up_metrics(override_session: None) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/analytics/ops")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["follow_up_queue"] == 2
    assert payload["high_priority_calls"] == 1
    assert payload["avg_lead_score"] > 0
