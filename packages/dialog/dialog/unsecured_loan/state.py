"""DialogState and supporting types — exact ADR 0002 §4 schema.

Do NOT add, rename, or remove fields without a corresponding ADR revision.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

# ── Slot set ──────────────────────────────────────────────────────────────────

class SlotSet(BaseModel):
    name_confirmed: bool = False
    has_time: Optional[bool] = None
    monthly_income_inr: Optional[int] = None
    loan_purpose: Optional[str] = None
    consent_given: Optional[bool] = None
    outcome: Optional[Literal[
        "qualified", "not_qualified", "no_consent", "callback_requested", "dropped"
    ]] = None


# ── Turn record ───────────────────────────────────────────────────────────────

class TurnRecord(BaseModel):
    speaker: Literal["agent", "customer"]
    text: str
    node_name: str
    turn_index: int


# ── Dialog node literal ───────────────────────────────────────────────────────

DialogNode = Literal[
    "opener",
    "identity_confirm",
    "qualify",
    "qualify_followup",
    "consent",
    "next_step",
    "close",
    "__end__",
]


# ── Dialog state ──────────────────────────────────────────────────────────────

class DialogState(BaseModel):
    call_id: str
    customer_id: str
    product: str = "unsecured_loan"
    agent_name: str
    lender_name: str
    customer_name: str

    current_node: DialogNode = "opener"
    history: list[TurnRecord] = Field(default_factory=list)
    slots: SlotSet = Field(default_factory=SlotSet)

    retry_count: int = 0
    error_count: int = 0
    turn_index: int = 0

    # Set externally by the pipeline before each node invocation.
    # Holds the most recent customer utterance (raw, not redacted).
    asr_text: str = ""
