"""DialogState serialisation round-trip — verifies Redis JSON compatibility."""
from __future__ import annotations

import json

from dialog.personal_loan.state import DialogState, SlotSet, TurnRecord
from tests.conftest import make_state


def test_empty_state_serialises_to_json() -> None:
    state = make_state()
    raw = state.model_dump_json()
    restored = DialogState.model_validate_json(raw)
    assert restored.call_id == state.call_id
    assert restored.slots == state.slots
    assert restored.history == []


def test_state_with_history_round_trips() -> None:
    state = make_state()
    turn = TurnRecord(speaker="agent", text="Namaste!", node_name="opener", turn_index=0)
    state = state.model_copy(update={"history": [turn], "turn_index": 1})

    raw = state.model_dump_json()
    restored = DialogState.model_validate_json(raw)

    assert len(restored.history) == 1
    assert restored.history[0].text == "Namaste!"
    assert restored.turn_index == 1


def test_slots_round_trip() -> None:
    slots = SlotSet(
        name_confirmed=True,
        has_time=True,
        monthly_income_inr=75000,
        loan_purpose="home_renovation",
        consent_given=True,
        outcome="qualified",
    )
    raw = slots.model_dump_json()
    restored = SlotSet.model_validate_json(raw)
    assert restored == slots


def test_state_dict_serialisation_is_json_safe() -> None:
    """model_dump() should produce a plain dict that json.dumps handles without error."""
    state = make_state()
    state = state.model_copy(update={
        "slots": SlotSet(monthly_income_inr=50000, consent_given=True, outcome="qualified"),
        "retry_count": 1,
        "asr_text": "test utterance",
    })
    d = state.model_dump()
    # Must not raise
    raw = json.dumps(d, default=str)
    parsed = json.loads(raw)
    assert parsed["slots"]["monthly_income_inr"] == 50000


def test_model_copy_does_not_mutate_original() -> None:
    original = make_state()
    updated = original.model_copy(update={"retry_count": 5})
    assert original.retry_count == 0
    assert updated.retry_count == 5
