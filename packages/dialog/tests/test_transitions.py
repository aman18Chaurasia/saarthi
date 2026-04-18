"""Unit tests for each transition function — pure, no LLM, no LangGraph."""
from __future__ import annotations

import pytest

from dialog.personal_loan.state import DialogState, SlotSet
from dialog.personal_loan.transitions import (
    transition_close,
    transition_consent,
    transition_identity_confirm,
    transition_next_step,
    transition_opener,
    transition_qualify,
    transition_qualify_followup,
)
from tests.conftest import make_state


# ── transition_opener ─────────────────────────────────────────────────────────

def test_opener_always_goes_to_identity_confirm() -> None:
    assert transition_opener(make_state()) == "identity_confirm"


# ── transition_identity_confirm ──────────────────────────────────────────────��

def _ic_state(**slot_kwargs: object) -> DialogState:
    return make_state().model_copy(update={"slots": SlotSet(**slot_kwargs)})  # type: ignore[arg-type]


def test_identity_confirm_advances_when_confirmed_and_has_time() -> None:
    s = _ic_state(name_confirmed=True, has_time=True)
    assert transition_identity_confirm(s) == "qualify"


def test_identity_confirm_closes_when_no_time() -> None:
    s = _ic_state(name_confirmed=True, has_time=False)
    assert transition_identity_confirm(s) == "close"


def test_identity_confirm_retries_when_unclear_within_budget() -> None:
    s = make_state().model_copy(update={"retry_count": 1})
    assert transition_identity_confirm(s) == "identity_confirm"


def test_identity_confirm_closes_when_retries_exceeded() -> None:
    s = make_state().model_copy(update={"retry_count": 3})
    assert transition_identity_confirm(s) == "close"


def test_identity_confirm_at_budget_boundary_retries() -> None:
    s = make_state().model_copy(update={"retry_count": 2})
    assert transition_identity_confirm(s) == "identity_confirm"


# ── transition_qualify ────────────────────────────────────────────────────────

def test_qualify_advances_when_income_captured() -> None:
    s = make_state().model_copy(update={"slots": SlotSet(monthly_income_inr=50000)})
    assert transition_qualify(s) == "qualify_followup"


def test_qualify_retries_when_income_missing_within_budget() -> None:
    s = make_state().model_copy(update={"retry_count": 1})
    assert transition_qualify(s) == "qualify"


def test_qualify_closes_after_budget_exhausted() -> None:
    s = make_state().model_copy(update={"retry_count": 3})
    assert transition_qualify(s) == "close"


def test_qualify_advances_even_with_high_retry_count_if_income_present() -> None:
    """Slot presence takes priority over retry_count."""
    s = make_state().model_copy(update={
        "slots": SlotSet(monthly_income_inr=80000),
        "retry_count": 3,
    })
    assert transition_qualify(s) == "qualify_followup"


# ── transition_qualify_followup ───────────────────────────────────────────────

def test_qualify_followup_advances_when_purpose_captured() -> None:
    s = make_state().model_copy(update={"slots": SlotSet(loan_purpose="travel")})
    assert transition_qualify_followup(s) == "consent"


def test_qualify_followup_retries_when_purpose_missing() -> None:
    s = make_state().model_copy(update={"retry_count": 0})
    assert transition_qualify_followup(s) == "qualify_followup"


def test_qualify_followup_closes_after_budget() -> None:
    s = make_state().model_copy(update={"retry_count": 3})
    assert transition_qualify_followup(s) == "close"


# ── transition_consent ────────────────────────────────────────────────────────

def test_consent_advances_when_granted() -> None:
    s = make_state().model_copy(update={"slots": SlotSet(consent_given=True)})
    assert transition_consent(s) == "next_step"


def test_consent_closes_when_denied() -> None:
    s = make_state().model_copy(update={"slots": SlotSet(consent_given=False)})
    assert transition_consent(s) == "close"


def test_consent_retries_when_unclear() -> None:
    s = make_state().model_copy(update={"retry_count": 1})
    assert transition_consent(s) == "consent"


def test_consent_closes_after_budget() -> None:
    s = make_state().model_copy(update={"retry_count": 3})
    assert transition_consent(s) == "close"


# ── transition_next_step + transition_close ───────────────────────────────────

def test_next_step_always_goes_to_close() -> None:
    assert transition_next_step(make_state()) == "close"


def test_close_always_goes_to_end() -> None:
    assert transition_close(make_state()) == "__end__"
