"""create_calls_table

Revision ID: f10792c455de
Revises:
Create Date: 2026-04-18 15:03:04.534186

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f10792c455de"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calls",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("call_id", sa.String(), nullable=False),
        sa.Column("customer_id", sa.String(), nullable=False),
        sa.Column("product", sa.String(), nullable=False),
        sa.Column("agent_name", sa.String(), nullable=False),
        sa.Column("lender_name", sa.String(), nullable=False),
        sa.Column("customer_name_redacted", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("outcome", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("duration_s", sa.Float(), nullable=True),
        sa.Column("turn_count", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("audio_failed", sa.Boolean(), nullable=False),
        sa.Column(
            "transcript_redacted",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "latency_stats",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "slots_redacted",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_calls_call_id"), "calls", ["call_id"], unique=True)
    op.create_index(op.f("ix_calls_customer_id"), "calls", ["customer_id"], unique=False)
    op.create_index(op.f("ix_calls_id"), "calls", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_calls_id"), table_name="calls")
    op.drop_index(op.f("ix_calls_customer_id"), table_name="calls")
    op.drop_index(op.f("ix_calls_call_id"), table_name="calls")
    op.drop_table("calls")
