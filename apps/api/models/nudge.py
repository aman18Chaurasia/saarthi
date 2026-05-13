from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class NudgeTemplate(SQLModel, table=True):
    """Product-wise nudge templates for agent assistance."""

    __tablename__ = "nudge_templates"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )
    product: str = Field(index=True)  # personal_loan, home_loan, etc
    trigger_type: str = Field(index=True)  # "objection" | "product_fact" | "eligibility" | "process"
    trigger_keywords: list[str] = Field(
        default=[],
        sa_column=Column(JSONB, nullable=False, server_default=text("'[]'::jsonb")),
    )

    title: str
    suggestion: str
    priority: str = "medium"  # "low" | "medium" | "high"

    enabled: bool = True
    confidence_threshold: float = 0.7

    # Metadata for routing/classification
    meta_info: dict[str, str] = Field(
        default={},
        sa_column=Column(JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Nudge(SQLModel, table=True):
    """Realtime nudges generated during call transcription."""

    __tablename__ = "nudges"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )
    call_id: str = Field(index=True)
    template_id: Optional[uuid.UUID] = Field(default=None, foreign_key="nudge_templates.id")

    product: str = Field(index=True)
    route: str  # "PRODUCT_FACT" | "OBJECTION" | "ELIGIBILITY" | "NONE"

    # Nudge content
    title: str
    suggestion: str
    priority: str
    priority_score: float = 0.5
    confidence: float

    # Context
    transcript_chunk: str
    speaker: str = "customer"
    audio_id: Optional[str] = None

    # Decision metadata
    emitted: bool = True
    suppression_reason: Optional[str] = None

    # Policy checks
    policy_checks: dict[str, bool] = Field(
        default={},
        sa_column=Column(JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)


class NudgeHistory(SQLModel, table=True):
    """Analytics and audit trail for nudge effectiveness."""

    __tablename__ = "nudge_history"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )
    nudge_id: uuid.UUID = Field(foreign_key="nudges.id", index=True)
    call_id: str = Field(index=True)

    # Agent interaction
    viewed: bool = False
    viewed_at: Optional[datetime] = None
    dismissed: bool = False
    dismissed_at: Optional[datetime] = None
    used: bool = False  # agent explicitly used the suggestion
    used_at: Optional[datetime] = None

    # Effectiveness tracking
    helped: Optional[bool] = None  # agent feedback
    feedback_text: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
