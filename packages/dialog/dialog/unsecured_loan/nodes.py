"""Async node functions for the personal loan dialog graph.

Each node:
  - Receives DialogState (immutable — do NOT mutate in place).
  - Calls the injected LLM callable once with Groq JSON-mode messages.
  - Returns state.model_copy(update={...}) with updated slots, history, counters.
  - On LLM failure / JSON parse error: falls back to classified_intent='unclear'
    and increments retry_count.

The LLM callable is injected at graph-build time (see graph.py) so tests can
substitute a mock without touching any network.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Awaitable

from pydantic import ValidationError

from .prompts import build_messages, get_fallback_text
from .schema import StructuredAgentResponse
from .state import DialogNode, DialogState, SlotSet, TurnRecord

# Type alias for the injected LLM callable
LLMCallable = Callable[
    [list[dict[str, str]], str, str],   # (messages, node_name, asr_text)
    Awaitable[StructuredAgentResponse],
]


# ── Shared helpers ────────────────────────────────────────────────────────────

def _build_messages(state: DialogState, node_name: str) -> list[dict[str, str]]:
    return build_messages(
        agent_name=state.agent_name,
        lender_name=state.lender_name,
        customer_name=state.customer_name,
        node_name=node_name,
        asr_text=state.asr_text,
    )


async def _call_llm(
    llm_fn: LLMCallable,
    state: DialogState,
    node_name: str,
) -> StructuredAgentResponse:
    """Call the LLM and return a validated StructuredAgentResponse.

    On any failure returns a fallback 'unclear' response without raising.
    """
    messages = _build_messages(state, node_name)
    try:
        resp = await llm_fn(messages, node_name, state.asr_text)
        # Re-validate in case the mock/LLM returns a raw dict
        if isinstance(resp, dict):
            return StructuredAgentResponse.model_validate(resp)
        return resp
    except (json.JSONDecodeError, ValidationError, KeyError, TypeError, ValueError):
        return StructuredAgentResponse(
            classified_intent="unclear",
            slots_extracted={},
            agent_turn_text=get_fallback_text(
                node_name,
                state.agent_name,
                state.lender_name,
                state.customer_name,
            ),
        )


def _append_turns(
    state: DialogState,
    node_name: str,
    agent_text: str,
    *,
    include_customer: bool = True,
) -> tuple[list[TurnRecord], int]:
    """Return (new_history, new_turn_index) with customer + agent turns appended."""
    history = list(state.history)
    ti = state.turn_index

    if include_customer and state.asr_text:
        history.append(TurnRecord(
            speaker="customer",
            text=state.asr_text,
            node_name=node_name,
            turn_index=ti,
        ))
        ti += 1

    history.append(TurnRecord(
        speaker="agent",
        text=agent_text,
        node_name=node_name,
        turn_index=ti,
    ))
    return history, ti + 1


def _was_useful(resp: StructuredAgentResponse, updated_slots: SlotSet, node_name: str) -> bool:
    """Return True when the LLM response contributed useful information for this node."""
    if resp.classified_intent == "unclear":
        return False
    if node_name == "identity_confirm":
        return updated_slots.has_time is not None
    if node_name == "qualify":
        return updated_slots.monthly_income_inr is not None
    if node_name == "qualify_followup":
        return updated_slots.loan_purpose is not None
    if node_name == "consent":
        return updated_slots.consent_given is not None
    # opener, next_step, close — always considered useful (no retries)
    return True


def _update_slots(current: SlotSet, extracted: dict[str, Any]) -> SlotSet:
    """Merge extracted slot values into the current SlotSet, ignoring unknown keys."""
    valid_fields = SlotSet.model_fields
    safe = {k: v for k, v in extracted.items() if k in valid_fields}
    return current.model_copy(update=safe) if safe else current


# ── Node functions ────────────────────────────────────────────────────────────

async def opener_node(state: DialogState, llm_fn: LLMCallable) -> DialogState:
    """Fires at call start — no customer input yet."""
    resp = await _call_llm(llm_fn, state, "opener")
    history, ti = _append_turns(state, "opener", resp.agent_turn_text, include_customer=False)
    return state.model_copy(update={
        "current_node": "opener",
        "history": history,
        "turn_index": ti,
        "retry_count": 0,
    })


async def identity_confirm_node(state: DialogState, llm_fn: LLMCallable) -> DialogState:
    resp = await _call_llm(llm_fn, state, "identity_confirm")
    new_slots = _update_slots(state.slots, resp.slots_extracted)
    useful = _was_useful(resp, new_slots, "identity_confirm")
    history, ti = _append_turns(state, "identity_confirm", resp.agent_turn_text)
    return state.model_copy(update={
        "current_node": "identity_confirm",
        "history": history,
        "slots": new_slots,
        "retry_count": 0 if useful else state.retry_count + 1,
        "turn_index": ti,
    })


async def qualify_node(state: DialogState, llm_fn: LLMCallable) -> DialogState:
    resp = await _call_llm(llm_fn, state, "qualify")
    new_slots = _update_slots(state.slots, resp.slots_extracted)
    useful = _was_useful(resp, new_slots, "qualify")
    history, ti = _append_turns(state, "qualify", resp.agent_turn_text)
    return state.model_copy(update={
        "current_node": "qualify",
        "history": history,
        "slots": new_slots,
        "retry_count": 0 if useful else state.retry_count + 1,
        "turn_index": ti,
    })


async def qualify_followup_node(state: DialogState, llm_fn: LLMCallable) -> DialogState:
    resp = await _call_llm(llm_fn, state, "qualify_followup")
    new_slots = _update_slots(state.slots, resp.slots_extracted)
    useful = _was_useful(resp, new_slots, "qualify_followup")
    history, ti = _append_turns(state, "qualify_followup", resp.agent_turn_text)
    return state.model_copy(update={
        "current_node": "qualify_followup",
        "history": history,
        "slots": new_slots,
        "retry_count": 0 if useful else state.retry_count + 1,
        "turn_index": ti,
    })


async def consent_node(state: DialogState, llm_fn: LLMCallable) -> DialogState:
    resp = await _call_llm(llm_fn, state, "consent")
    new_slots = _update_slots(state.slots, resp.slots_extracted)
    useful = _was_useful(resp, new_slots, "consent")
    history, ti = _append_turns(state, "consent", resp.agent_turn_text)
    return state.model_copy(update={
        "current_node": "consent",
        "history": history,
        "slots": new_slots,
        "retry_count": 0 if useful else state.retry_count + 1,
        "turn_index": ti,
    })


async def next_step_node(state: DialogState, llm_fn: LLMCallable) -> DialogState:
    resp = await _call_llm(llm_fn, state, "next_step")
    history, ti = _append_turns(state, "next_step", resp.agent_turn_text, include_customer=False)
    return state.model_copy(update={
        "current_node": "next_step",
        "history": history,
        "retry_count": 0,
        "turn_index": ti,
    })


def _determine_outcome(state: DialogState) -> str:
    s = state.slots
    if s.consent_given is True and s.monthly_income_inr is not None:
        return "qualified"
    if s.consent_given is False:
        return "no_consent"
    if s.has_time is False:
        return "dropped"
    return "dropped"


async def close_node(state: DialogState, llm_fn: LLMCallable) -> DialogState:
    resp = await _call_llm(llm_fn, state, "close")
    outcome = _determine_outcome(state)
    new_slots = state.slots.model_copy(update={"outcome": outcome})
    history, ti = _append_turns(state, "close", resp.agent_turn_text, include_customer=False)
    return state.model_copy(update={
        "current_node": "close",
        "history": history,
        "slots": new_slots,
        "turn_index": ti,
    })
