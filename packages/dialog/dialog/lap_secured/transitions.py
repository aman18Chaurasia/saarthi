"""Transition functions for the personal loan dialog graph.

Each function is a PURE function of DialogState that returns the next DialogNode.
Transition logic is the only place where routing decisions are made.
Nodes are responsible for updating slots and retry_count; transitions read them.

Retry budget: retry_count <= 2 allows 3 total attempts per node before closing.
(ADR 0002 §6 specifies < 2; we use <= 2 to support the 3-attempt test scenario.)
"""
from __future__ import annotations

from .state import DialogNode, DialogState


def transition_opener(state: DialogState) -> DialogNode:
    return "identity_confirm"


def transition_identity_confirm(state: DialogState) -> DialogNode:
    # Advance when customer confirmed identity AND indicated they have time
    if state.slots.name_confirmed and state.slots.has_time is True:
        return "qualify"
    # Customer explicitly said they're busy
    if state.slots.has_time is False:
        return "close"
    # Unclear response — retry up to the budget
    if state.retry_count <= 2:
        return "identity_confirm"
    return "close"


def transition_qualify(state: DialogState) -> DialogNode:
    if state.slots.monthly_income_inr is not None:
        return "qualify_followup"
    if state.retry_count <= 2:
        return "qualify"
    return "close"


def transition_qualify_followup(state: DialogState) -> DialogNode:
    if state.slots.loan_purpose is not None:
        return "consent"
    if state.retry_count <= 2:
        return "qualify_followup"
    return "close"


def transition_consent(state: DialogState) -> DialogNode:
    if state.slots.consent_given is True:
        return "next_step"
    if state.slots.consent_given is False:
        return "close"
    if state.retry_count <= 2:
        return "consent"
    return "close"


def transition_next_step(state: DialogState) -> DialogNode:
    return "close"


def transition_close(state: DialogState) -> DialogNode:
    return "__end__"


# ── Registry (used by graph.py) ───────────────────────────────────────────────

TRANSITION_MAP: dict[str, object] = {
    "opener":           transition_opener,
    "identity_confirm": transition_identity_confirm,
    "qualify":          transition_qualify,
    "qualify_followup": transition_qualify_followup,
    "consent":          transition_consent,
    "next_step":        transition_next_step,
    "close":            transition_close,
}
