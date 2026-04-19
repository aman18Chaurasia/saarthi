"""Multi-agent architecture: Supervisor + Qualifier + Objection Handler."""
from __future__ import annotations

from typing import Literal

from .nodes import LLMCallable
from .state import DialogState


async def supervisor_node(state: DialogState, llm_fn: LLMCallable) -> DialogState:
    """Route to Qualifier or Objection Handler based on customer intent."""
    # Simple routing: if customer asks questions/objects, route to objection handler
    asr = state.asr_text.lower()

    # Objection keywords
    if any(kw in asr for kw in ["why", "expensive", "high interest", "better rate", "no thanks"]):
        return state.model_copy(update={"agent_mode": "objection_handler"})

    # Default to qualifier
    return state.model_copy(update={"agent_mode": "qualifier"})


async def objection_handler_node(state: DialogState, llm_fn: LLMCallable) -> DialogState:
    """Handle customer objections with empathy and data."""
    from .prompts import build_messages
    from .nodes import _call_llm, _append_turns

    # Build objection handling prompt
    objection_prompt = f"""
    Customer objection: {state.asr_text}

    Respond with empathy and facts. Acknowledge concern, provide brief value prop.
    Keep response under 25 words.
    """

    resp = await _call_llm(llm_fn, state, state.current_node)
    history, ti = _append_turns(state, state.current_node, resp.agent_turn_text)

    return state.model_copy(update={
        "history": history,
        "turn_index": ti,
        "agent_mode": "qualifier"  # Return to qualifier after handling
    })


def route_agent_mode(state: DialogState) -> Literal["qualifier", "objection_handler"]:
    """Route based on agent_mode."""
    return state.agent_mode if hasattr(state, "agent_mode") else "qualifier"
