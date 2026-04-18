from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class Call(SQLModel, table=True):
    __tablename__ = "calls"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )
    call_id: str = Field(index=True, unique=True)
    customer_id: str = Field(index=True)
    product: str  # "personal_loan"
    agent_name: str
    lender_name: str
    customer_name_redacted: str

    status: str  # "in_progress" | "completed" | "dropped"
    outcome: Optional[str] = None  # "qualified" | "not_qualified" | "no_consent" | "callback_requested" | "dropped"

    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    duration_s: Optional[float] = None

    turn_count: int = 0
    error_count: int = 0
    audio_failed: bool = False

    # Presidio-redacted full transcript: [{speaker, text, node, turn_index}]
    transcript_redacted: list[dict[str, Any]] = Field(
        default=[],
        sa_column=Column(JSONB, nullable=False, server_default=text("'[]'::jsonb")),
    )

    # p50/p95 per hop: {asr_p50, asr_p95, llm_p50, llm_p95, tts_p50, tts_p95, e2e_p50, e2e_p95}
    latency_stats: dict[str, float] = Field(
        default={},
        sa_column=Column(JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    )

    # Non-PII slot values captured during the call (post-redaction)
    slots_redacted: dict[str, Any] = Field(
        default={},
        sa_column=Column(JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    )
