from __future__ import annotations

import uuid

import pytest

from dialog.home_loan.graph import build_graph
from dialog.home_loan.nodes import qualify_followup_node
from dialog.home_loan.schema import StructuredAgentResponse
from dialog.home_loan.state import DialogState, SlotSet
from dialog.home_loan.transitions import transition_qualify_followup
from tests.conftest import ConversationRunner, mock_llm_for


def _make_state(**kwargs: object) -> DialogState:
    defaults = {
        "call_id": f"home-loan-{uuid.uuid4().hex[:8]}",
        "customer_id": "cust-001",
        "agent_name": "Priya",
        "lender_name": "Demo Bank",
        "customer_name": "Rahul",
    }
    defaults.update(kwargs)
    return DialogState(**defaults)


def _resp(
    intent: str = "provide_value",
    slots: dict[str, object] | None = None,
    text: str = "Agent says.",
) -> StructuredAgentResponse:
    return StructuredAgentResponse(
        classified_intent=intent,  # type: ignore[arg-type]
        slots_extracted=slots or {},
        agent_turn_text=text,
    )


@pytest.mark.asyncio
async def test_home_loan_followup_extracts_property_details() -> None:
    state = _make_state(asr_text="Pune mein flat dekh raha hoon, budget 80 lakh hai")
    llm = mock_llm_for(
        {
            "qualify_followup": _resp(
                slots={
                    "city": "Pune",
                    "property_value_inr": 8000000,
                    "property_type": "residential",
                },
                text="Theek hai, Pune aur 80 lakh noted.",
            )
        }
    )

    result = await qualify_followup_node(state, llm)

    assert result.slots.city == "Pune"
    assert result.slots.property_value_inr == 8000000
    assert result.slots.property_type == "residential"
    assert result.retry_count == 0


def test_home_loan_followup_advances_when_value_and_city_present() -> None:
    state = _make_state(
        slots=SlotSet(property_value_inr=8000000, city="Pune", property_type="residential")
    )
    assert transition_qualify_followup(state) == "consent"


def test_home_loan_followup_retries_when_value_or_city_missing() -> None:
    state = _make_state(slots=SlotSet(property_value_inr=8000000), retry_count=1)
    assert transition_qualify_followup(state) == "qualify_followup"


@pytest.mark.asyncio
async def test_home_loan_graph_reaches_consent_after_property_details() -> None:
    llm = mock_llm_for(
        {
            "opener": _resp(intent="unclear", text="Namaste! Kya aap Rahul ji bol rahe hain?"),
            "identity_confirm": _resp(
                intent="affirm",
                slots={"name_confirmed": True, "has_time": True},
                text="Bas 2 minute lagenge. Aapki income kitni hai?",
            ),
            "qualify": _resp(
                intent="provide_value",
                slots={"monthly_income_inr": 50000},
                text="Aur property kis city mein aur kitne budget ki dekh rahe hain?",
            ),
            "qualify_followup": _resp(
                intent="provide_value",
                slots={"city": "Pune", "property_value_inr": 8000000},
                text="Samajh gaya. Kya aap consent dete hain?",
            ),
        }
    )

    runner = await ConversationRunner.create(build_graph(llm), _make_state())

    await runner.say("Haan Rahul bol raha hoon")
    await runner.say("50,000")
    await runner.say("Pune mein flat, around 80 lakh")

    assert runner.current_node == "qualify_followup"
    assert runner.slots.city == "Pune"
    assert runner.slots.property_value_inr == 8000000
    assert any(turn.node_name == "qualify_followup" for turn in runner.history)
