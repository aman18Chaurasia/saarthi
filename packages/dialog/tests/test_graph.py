"""End-to-end graph tests — drives the compiled LangGraph through full conversations.

Each test uses ConversationRunner to manage interrupt/resume cycles.
No network calls: all LLM responses are mocked.
Tests are async because LangGraph nodes are async (ainvoke required).
"""
from __future__ import annotations

import pytest

from dialog.personal_loan.graph import build_graph
from dialog.personal_loan.schema import StructuredAgentResponse
from tests.conftest import ConversationRunner, make_state, mock_llm_for, sequence_llm_for


def _r(intent: str, slots: dict = {}, text: str = "Agent says.") -> StructuredAgentResponse:
    return StructuredAgentResponse(
        classified_intent=intent,  # type: ignore[arg-type]
        slots_extracted=slots,
        agent_turn_text=text,
    )


# ── Test a: Happy path ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_happy_path_reaches_qualified() -> None:
    """opener → identity_confirm → qualify → qualify_followup → consent → next_step → close.
    Final outcome must be 'qualified'.
    """
    llm = mock_llm_for({
        "opener":           _r("unclear",       {},                          "Namaste! Kya aap Priya ji hain?"),
        "identity_confirm": _r("affirm",         {"name_confirmed": True, "has_time": True},
                                "Thank you. Loan offer ke baare mein baat karein?"),
        "qualify":          _r("provide_value",  {"monthly_income_inr": 60000},
                                "Great, 60k noted. Loan kisliye?"),
        "qualify_followup": _r("provide_value",  {"loan_purpose": "home_renovation"},
                                "Samajh gaya. Consent details share karta hoon."),
        "consent":          _r("affirm",         {"consent_given": True},
                                "Shukriya. Offer 24 ghante mein aayega."),
        "next_step":        _r("affirm",         {},
                                "Perfect. 24 ghante mein SMS aayega."),
        "close":            _r("unclear",        {},
                                "Bahut shukriya! Have a great day!"),
    })

    runner = await ConversationRunner.create(build_graph(llm), make_state())

    await runner.say("Haan ji, main Priya hoon")          # identity_confirm
    await runner.say("Mere paas time hai")                 # qualify
    await runner.say("60000")                              # qualify_followup
    await runner.say("Ghar ke liye")                       # consent
    await runner.say("Haan, consent deta hoon")            # next_step
    await runner.advance()                                 # close (no customer input)

    assert runner.outcome == "qualified"
    nodes_in_history = {t.node_name for t in runner.history if t.speaker == "agent"}
    assert nodes_in_history == {
        "opener", "identity_confirm", "qualify", "qualify_followup",
        "consent", "next_step", "close",
    }


# ── Test b: Retry path ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_retry_path_qualify_unclear_twice_then_succeeds() -> None:
    """qualify receives unclear input twice, then income on the 3rd attempt.
    Final outcome must be 'qualified'.
    """
    llm = sequence_llm_for({
        "opener":           [_r("unclear", {}, "Namaste!")],
        "identity_confirm": [_r("affirm",  {"name_confirmed": True, "has_time": True},
                                "Thank you, let's proceed.")],
        "qualify": [
            _r("unclear",       {},             "Sorry, could you repeat your income?"),
            _r("unclear",       {},             "Approximately kitni income hai?"),
            _r("provide_value", {"monthly_income_inr": 45000}, "45k, noted."),
        ],
        "qualify_followup": [_r("provide_value", {"loan_purpose": "medical"}, "Medical, understood.")],
        "consent":          [_r("affirm",  {"consent_given": True}, "Shukriya.")],
        "next_step":        [_r("affirm",  {},                      "Offer 24h mein aayega.")],
        "close":            [_r("unclear", {},                      "Have a great day!")],
    })

    runner = await ConversationRunner.create(build_graph(llm), make_state())

    await runner.say("Haan, main hoon aur time hai")   # identity_confirm
    await runner.say("pata nahi")                       # qualify attempt 1 (unclear)
    await runner.say("ugh")                             # qualify attempt 2 (unclear)
    await runner.say("45000")                           # qualify attempt 3 (success)
    await runner.say("medical")                         # qualify_followup
    await runner.say("haan")                            # consent → interrupt
    await runner.advance()                              # next_step → interrupt
    await runner.advance()                              # close → END

    assert runner.outcome == "qualified"
    qualify_turns = [t for t in runner.history if t.node_name == "qualify" and t.speaker == "agent"]
    assert len(qualify_turns) == 3, f"Expected 3 qualify agent turns, got {len(qualify_turns)}"


# ── Test c: No-consent path ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_no_consent_path_sets_outcome_no_consent() -> None:
    """Customer reaches consent node, explicitly denies → outcome='no_consent'."""
    llm = mock_llm_for({
        "opener":           _r("unclear",       {},                           "Namaste!"),
        "identity_confirm": _r("affirm",         {"name_confirmed": True, "has_time": True},
                                "Thank you."),
        "qualify":          _r("provide_value",  {"monthly_income_inr": 50000}, "50k noted."),
        "qualify_followup": _r("provide_value",  {"loan_purpose": "travel"},    "Travel, noted."),
        "consent":          _r("deny",           {"consent_given": False},
                                "Samajh gaya, koi baat nahi."),
        "close":            _r("unclear",        {},
                                "Theek hai, baad mein phir baat karte hain. Dhanyavaad!"),
    })

    runner = await ConversationRunner.create(build_graph(llm), make_state())

    await runner.say("Haan, main hoon")
    await runner.say("iske paas time hai")
    await runner.say("50000")
    await runner.say("travel")
    await runner.say("nahi, mujhe consent nahi dena")    # consent denied → close

    assert runner.outcome == "no_consent"
    nodes_ran = {t.node_name for t in runner.history if t.speaker == "agent"}
    assert "next_step" not in nodes_ran


# ── Test d: Busy-customer path ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_busy_customer_path_drops_after_identity_confirm() -> None:
    """Customer says they don't have time during identity_confirm → outcome='dropped'."""
    llm = mock_llm_for({
        "opener":           _r("unclear", {}, "Namaste! Kya aap Priya ji hain?"),
        "identity_confirm": _r("deny",    {"name_confirmed": True, "has_time": False},
                               "Theek hai, baad mein phir call karenge."),
        "close":            _r("unclear", {}, "Shukriya, have a great day!"),
    })

    runner = await ConversationRunner.create(build_graph(llm), make_state())

    await runner.say("Haan main hoon, par abhi busy hoon")    # identity_confirm: has_time=False
    await runner.advance()                                     # transition_IC → close → END

    assert runner.outcome == "dropped"
    nodes_ran = {t.node_name for t in runner.history if t.speaker == "agent"}
    assert "qualify" not in nodes_ran
    assert "consent" not in nodes_ran
