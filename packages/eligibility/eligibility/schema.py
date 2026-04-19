"""Pydantic schemas for eligibility engine."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class EligibilityResult(BaseModel):
    """Result of an eligibility check."""
    eligible: bool
    reasons: list[str] = Field(default_factory=list)
    source: Literal["neo4j", "fallback"] = "neo4j"
    matched_rules: int = 0


class ProductRule(BaseModel):
    """A single eligibility rule from Neo4j."""
    rule_id: str
    rule_type: str
    threshold_value: int | float | None = None
    operator: str | None = None  # gte, lte, eq
    error_message: str
