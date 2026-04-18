"""Unit tests — each node receives state, calls mock LLM, returns correct mutations."""
from __future__ import annotations

import pytest

from dialog.personal_loan.nodes import (
    close_node,
    consent_node,
    identity_confirm_node,
    next_step_node,
    opener_node,
    qualify_followup_node,
    qualify_node,
)
from dialog.personal_loan.schema import StructuredAgentResponse
from dialog.personal_loan.state import DialogState, SlotSet
from tests.conftest import make_state, mock_llm_for


def _r(intent: str = "provide_value", slots: dict = {}, text: str = "Agent says.") -> StructuredAgentResponse:
    return StructuredAgentResponse(
        classified_intent=intent,  # type: ignore[arg-type]
        slots_extracted=slots,
        agent_turn_text=text,
    )


# ── opener ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_opener_appends_agent_turn() -> None:
    state = make_state()
    llm = mock_llm_for({"opener": _r(text="Namaste!")})
    result = await opener_node(state, llm)

    assert result.current_node == "opener"
    assert len(result.history) == 1
    assert result.history[0].speaker == "agent"
    assert result.history[0].text == "Namaste!"
    assert result.turn_index == 1


@pytest.mark.asyncio
async def test_opener_does_not_include_empty_customer_turn() -> None:
    state = make_state(asr_text="")
    llm = mock_llm_for({"opener": _r()})
    result = await opener_node(state, llm)
    assert all(t.speaker == "agent" for t in result.history)


@pytest.mark.asyncio
async def test_opener_does_not_mutate_original_state() -> None:
    state = make_state()
    llm = mock_llm_for({"opener": _r()})
    result = await opener_node(state, llm)
    assert state.history == []
    assert result is not state


# ── identity_confirm ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_identity_confirm_sets_slots_on_affirm() -> None:
    state = make_state(asr_text="Haan ji, main hoon")
    llm = mock_llm_for({"identity_confirm": _r(
        intent="affirm",
        slots={"name_confirmed": True, "has_time": True},
        text="Theek hai, main ek offer share karta hoon.",
    )})
    result = await identity_confirm_node(state, llm)

    assert result.slots.name_confirmed is True
    assert result.slots.has_time is True
    assert result.retry_count == 0


@pytest.mark.asyncio
async def test_identity_confirm_increments_retry_on_unclear() -> None:
    state = make_state(asr_text="Kya?", retry_count=0)
    llm = mock_llm_for({"identity_confirm": _r(intent="unclear", text="Kya aap confirm kar sakte hain?")})
    result = await identity_confirm_node(state, llm)
    assert result.retry_count == 1
    assert result.slots.has_time is None


@pytest.mark.asyncio
async def test_identity_confirm_appends_customer_and_agent_turns() -> None:
    state = make_state(asr_text="Ji haan")
    llm = mock_llm_for({"identity_confirm": _r(intent="affirm", slots={"name_confirmed": True, "has_time": True})})
    result = await identity_confirm_node(state, llm)
    speakers = [t.speaker for t in result.history]
    assert speakers == ["customer", "agent"]


# ── qualify ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_qualify_extracts_income() -> None:
    state = make_state(asr_text="Meri income 60 hazaar hai")
    llm = mock_llm_for({"qualify": _r(
        intent="provide_value",
        slots={"monthly_income_inr": 60000},
        text="Acha, 60,000 per month. Loan ka purpose?",
    )})
    result = await qualify_node(state, llm)
    assert result.slots.monthly_income_inr == 60000
    assert result.retry_count == 0


@pytest.mark.asyncio
async def test_qualify_increments_retry_when_no_income() -> None:
    state = make_state(asr_text="Pata nahi", retry_count=1)
    llm = mock_llm_for({"qualify": _r(intent="unclear", text="Approximately kitni hogi?")})
    result = await qualify_node(state, llm)
    assert result.slots.monthly_income_inr is None
    assert result.retry_count == 2


# ── qualify_followup ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_qualify_followup_extracts_purpose() -> None:
    state = make_state(asr_text="Ghar renovation ke liye")
    llm = mock_llm_for({"qualify_followup": _r(
        intent="provide_value",
        slots={"loan_purpose": "home_renovation"},
        text="Samajh gaya. Aapko ek tailored offer milega.",
    )})
    result = await qualify_followup_node(state, llm)
    assert result.slots.loan_purpose == "home_renovation"
    assert result.retry_count == 0


# ── consent ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_consent_sets_consent_true_on_affirm() -> None:
    state = make_state(asr_text="Haan, consent deta hoon")
    llm = mock_llm_for({"consent": _r(intent="affirm", slots={"consent_given": True})})
    result = await consent_node(state, llm)
    assert result.slots.consent_given is True
    assert result.retry_count == 0


@pytest.mark.asyncio
async def test_consent_sets_consent_false_on_deny() -> None:
    state = make_state(asr_text="Nahi chahiye")
    llm = mock_llm_for({"consent": _r(intent="deny", slots={"consent_given": False})})
    result = await consent_node(state, llm)
    assert result.slots.consent_given is False


# ── next_step ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_next_step_produces_agent_turn() -> None:
    state = make_state()
    llm = mock_llm_for({"next_step": _r(text="Aapko 24 ghante mein offer milega.")})
    result = await next_step_node(state, llm)
    assert result.current_node == "next_step"
    agent_turns = [t for t in result.history if t.speaker == "agent"]
    assert len(agent_turns) == 1
    assert "24 ghante" in agent_turns[0].text


# ── close ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_close_sets_outcome_qualified() -> None:
    state = make_state().model_copy(update={
        "slots": SlotSet(monthly_income_inr=50000, consent_given=True),
    })
    llm = mock_llm_for({"close": _r(text="Shukriya! Have a great day!")})
    result = await close_node(state, llm)
    assert result.slots.outcome == "qualified"


@pytest.mark.asyncio
async def test_close_sets_outcome_no_consent() -> None:
    state = make_state().model_copy(update={"slots": SlotSet(consent_given=False)})
    llm = mock_llm_for({"close": _r(text="Theek hai, koi baat nahi.")})
    result = await close_node(state, llm)
    assert result.slots.outcome == "no_consent"


@pytest.mark.asyncio
async def test_close_sets_outcome_dropped_when_busy() -> None:
    state = make_state().model_copy(update={"slots": SlotSet(has_time=False)})
    llm = mock_llm_for({"close": _r(text="Koi baat nahi, baad mein try karenge.")})
    result = await close_node(state, llm)
    assert result.slots.outcome == "dropped"


# ── JSON parse error fallback ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_node_falls_back_to_unclear_on_bad_llm_response() -> None:
    """If LLM callable raises an exception, node must NOT raise; retry_count increments."""
    async def _bad_llm(messages, node_name, asr_text):  # type: ignore[override]
        raise ValueError("Simulated JSON parse error")

    state = make_state(asr_text="50000", retry_count=0)
    result = await qualify_node(state, _bad_llm)

    assert result.slots.monthly_income_inr is None
    assert result.retry_count == 1  # incremented because useful=False on unclear
