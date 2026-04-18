from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://saarthi:saarthi@localhost:5432/saarthi",
)

# Convert plain postgresql:// to asyncpg driver form
_async_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(_async_url, echo=False, pool_pre_ping=True)

AsyncSessionLocal: sessionmaker = sessionmaker(  # type: ignore[type-arg]
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def create_all_tables() -> None:
    """Used only in tests — Alembic handles migrations in production."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def drop_all_tables() -> None:
    """Used only in tests."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
