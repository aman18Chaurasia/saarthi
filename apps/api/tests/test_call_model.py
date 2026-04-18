"""Round-trip insert/select for the Call SQLModel against the live Postgres instance.

Requires the docker-compose postgres service to be running and DATABASE_URL set
(or the default postgresql+asyncpg://saarthi:saarthi@localhost:5432/saarthi used).
Each test creates its own engine so there are no cross-test event-loop conflicts.
"""
from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from models.call import Call  # registers Call in SQLModel.metadata

_DB_URL = os.environ.get(
    "DATABASE_URL", "postgresql://saarthi:saarthi@localhost:5432/saarthi"
).replace("postgresql://", "postgresql+asyncpg://", 1)


@pytest.fixture()
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    factory: sessionmaker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[type-arg]

    async with factory() as s:
        yield s

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


from collections.abc import AsyncGenerator  # noqa: E402 (needed after fixture def)


def _make_call(call_id: str, **kwargs) -> Call:  # type: ignore[no-untyped-def]
    return Call(
        call_id=call_id,
        customer_id=kwargs.get("customer_id", "cust_001"),
        product="personal_loan",
        agent_name="Rohan",
        lender_name="TestBank",
        customer_name_redacted="<PERSON_REDACTED>",
        status=kwargs.get("status", "completed"),
        outcome=kwargs.get("outcome", "qualified"),
        **{k: v for k, v in kwargs.items() if k not in ("customer_id", "status", "outcome")},
    )


@pytest.mark.asyncio
async def test_insert_and_select_by_call_id(session: AsyncSession) -> None:
    uid = f"call_{uuid.uuid4().hex[:8]}"
    call = _make_call(uid)
    session.add(call)
    await session.commit()
    await session.refresh(call)
    assert call.id is not None

    result = await session.exec(select(Call).where(Call.call_id == uid))
    fetched = result.one()
    assert fetched.call_id == uid
    assert fetched.product == "personal_loan"
    assert fetched.status == "completed"
    assert fetched.outcome == "qualified"


@pytest.mark.asyncio
async def test_jsonb_defaults_are_empty_containers(session: AsyncSession) -> None:
    call = _make_call(f"call_{uuid.uuid4().hex[:8]}")
    session.add(call)
    await session.commit()
    await session.refresh(call)

    assert call.transcript_redacted == []
    assert call.latency_stats == {}
    assert call.slots_redacted == {}


@pytest.mark.asyncio
async def test_jsonb_columns_roundtrip(session: AsyncSession) -> None:
    uid = f"call_{uuid.uuid4().hex[:8]}"
    transcript = [{"speaker": "agent", "text": "Namaste!", "node": "opener", "turn_index": 0}]
    latency = {"asr_p50": 72.4, "e2e_p95": 289.1}
    slots = {"monthly_income_inr": 75000, "consent_given": True}

    call = _make_call(uid, transcript_redacted=transcript, latency_stats=latency, slots_redacted=slots)
    session.add(call)
    await session.commit()
    await session.refresh(call)

    result = await session.exec(select(Call).where(Call.call_id == uid))
    fetched = result.one()
    assert fetched.transcript_redacted == transcript
    assert fetched.latency_stats == pytest.approx(latency)
    assert fetched.slots_redacted == slots


@pytest.mark.asyncio
async def test_call_id_uniqueness_enforced(session: AsyncSession) -> None:
    from sqlalchemy.exc import IntegrityError

    uid = "dup_call_id"
    session.add(_make_call(uid))
    await session.commit()

    with pytest.raises(IntegrityError):
        session.add(_make_call(uid))
        await session.commit()
