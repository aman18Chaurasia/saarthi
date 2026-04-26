"""create_nudge_tables

Revision ID: a1b2c3d4e5f6
Revises: f10792c455de
Create Date: 2026-04-26 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f10792c455de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create nudge_templates table
    op.create_table(
        "nudge_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product", sa.String(), nullable=False),
        sa.Column("trigger_type", sa.String(), nullable=False),
        sa.Column(
            "trigger_keywords",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("suggestion", sa.String(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("confidence_threshold", sa.Float(), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_nudge_templates_id"), "nudge_templates", ["id"], unique=False)
    op.create_index(op.f("ix_nudge_templates_product"), "nudge_templates", ["product"], unique=False)
    op.create_index(op.f("ix_nudge_templates_trigger_type"), "nudge_templates", ["trigger_type"], unique=False)

    # Create nudges table
    op.create_table(
        "nudges",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("call_id", sa.String(), nullable=False),
        sa.Column("template_id", sa.Uuid(), nullable=True),
        sa.Column("product", sa.String(), nullable=False),
        sa.Column("route", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("suggestion", sa.String(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("priority_score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("transcript_chunk", sa.String(), nullable=False),
        sa.Column("speaker", sa.String(), nullable=False),
        sa.Column("audio_id", sa.String(), nullable=True),
        sa.Column("emitted", sa.Boolean(), nullable=False),
        sa.Column("suppression_reason", sa.String(), nullable=True),
        sa.Column(
            "policy_checks",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["nudge_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_nudges_id"), "nudges", ["id"], unique=False)
    op.create_index(op.f("ix_nudges_call_id"), "nudges", ["call_id"], unique=False)
    op.create_index(op.f("ix_nudges_product"), "nudges", ["product"], unique=False)

    # Create nudge_history table
    op.create_table(
        "nudge_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nudge_id", sa.Uuid(), nullable=False),
        sa.Column("call_id", sa.String(), nullable=False),
        sa.Column("viewed", sa.Boolean(), nullable=False),
        sa.Column("viewed_at", sa.DateTime(), nullable=True),
        sa.Column("dismissed", sa.Boolean(), nullable=False),
        sa.Column("dismissed_at", sa.DateTime(), nullable=True),
        sa.Column("used", sa.Boolean(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("helped", sa.Boolean(), nullable=True),
        sa.Column("feedback_text", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["nudge_id"], ["nudges.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_nudge_history_id"), "nudge_history", ["id"], unique=False)
    op.create_index(op.f("ix_nudge_history_nudge_id"), "nudge_history", ["nudge_id"], unique=False)
    op.create_index(op.f("ix_nudge_history_call_id"), "nudge_history", ["call_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_nudge_history_call_id"), table_name="nudge_history")
    op.drop_index(op.f("ix_nudge_history_nudge_id"), table_name="nudge_history")
    op.drop_index(op.f("ix_nudge_history_id"), table_name="nudge_history")
    op.drop_table("nudge_history")

    op.drop_index(op.f("ix_nudges_product"), table_name="nudges")
    op.drop_index(op.f("ix_nudges_call_id"), table_name="nudges")
    op.drop_index(op.f("ix_nudges_id"), table_name="nudges")
    op.drop_table("nudges")

    op.drop_index(op.f("ix_nudge_templates_trigger_type"), table_name="nudge_templates")
    op.drop_index(op.f("ix_nudge_templates_product"), table_name="nudge_templates")
    op.drop_index(op.f("ix_nudge_templates_id"), table_name="nudge_templates")
    op.drop_table("nudge_templates")
