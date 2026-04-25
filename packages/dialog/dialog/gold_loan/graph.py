"""LangGraph StateGraph for the personal loan dialog.

build_graph(llm_fn) → CompiledStateGraph

The returned graph:
  - Uses MemorySaver (in-memory) for per-call checkpointing — no DB required.
  - Interrupts after every node except 'close', allowing the pipeline to inject
    the next customer utterance into DialogState.asr_text before resuming.
  - All node functions are closed over the injected llm_fn, so tests can pass
    a mock without any network calls.

Usage (real pipeline):
    from dialog.personal_loan.graph import build_graph
    from packages.llm_client import get_chat_provider  # wired in commit 5+

    app = build_graph(groq_json_mode_fn)
    config = {"configurable": {"thread_id": call_id}}
    state = app.invoke(initial_dialog_state.model_dump(), config)
    # → pipeline injects asr_text, then:
    app.update_state(config, {"asr_text": transcript})
    state = app.invoke(None, config)

Usage (tests):
    See tests/conftest.py for the ConversationRunner helper.
"""
from __future__ import annotations
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from .nodes import (
    LLMCallable,
    close_node,
    consent_node,
    identity_confirm_node,
    next_step_node,
    opener_node,
    qualify_followup_node,
    qualify_node,
)
from .state import DialogState
from .transitions import (
    transition_close,
    transition_consent,
    transition_identity_confirm,
    transition_next_step,
    transition_opener,
    transition_qualify,
    transition_qualify_followup,
)

# Nodes that interrupt after running (pipeline injects asr_text, then resumes)
_INTERRUPT_AFTER = [
    "opener",
    "identity_confirm",
    "qualify",
    "qualify_followup",
    "consent",
    "next_step",
]


def build_graph(llm_fn: LLMCallable, rag_fn: Any | None = None) -> CompiledStateGraph:
    """Build and compile the personal loan dialog graph.

    Args:
        llm_fn: Async callable ``(messages, node_name, asr_text) -> StructuredAgentResponse``.
                Pass a mock in tests; pass a real Groq JSON-mode function in production.

    Returns:
        A compiled LangGraph StateGraph with MemorySaver checkpointing.
    """
    # Close over llm_fn so each wrapper matches LangGraph's (state,) signature
    async def _opener(state: DialogState) -> DialogState:
        return await opener_node(state, llm_fn, rag_fn=rag_fn)

    async def _identity_confirm(state: DialogState) -> DialogState:
        return await identity_confirm_node(state, llm_fn, rag_fn=rag_fn)

    async def _qualify(state: DialogState) -> DialogState:
        return await qualify_node(state, llm_fn, rag_fn=rag_fn)

    async def _qualify_followup(state: DialogState) -> DialogState:
        return await qualify_followup_node(state, llm_fn, rag_fn=rag_fn)

    async def _consent(state: DialogState) -> DialogState:
        return await consent_node(state, llm_fn, rag_fn=rag_fn)

    async def _next_step(state: DialogState) -> DialogState:
        return await next_step_node(state, llm_fn, rag_fn=rag_fn)

    async def _close(state: DialogState) -> DialogState:
        return await close_node(state, llm_fn, rag_fn=rag_fn)

    g: StateGraph = StateGraph(DialogState)

    g.add_node("opener",           _opener)
    g.add_node("identity_confirm", _identity_confirm)
    g.add_node("qualify",          _qualify)
    g.add_node("qualify_followup", _qualify_followup)
    g.add_node("consent",          _consent)
    g.add_node("next_step",        _next_step)
    g.add_node("close",            _close)

    g.set_entry_point("opener")

    # Conditional edges — each uses the corresponding pure transition function
    g.add_conditional_edges(
        "opener",
        transition_opener,
        {"identity_confirm": "identity_confirm"},
    )
    g.add_conditional_edges(
        "identity_confirm",
        transition_identity_confirm,
        {"qualify": "qualify", "identity_confirm": "identity_confirm", "close": "close"},
    )
    g.add_conditional_edges(
        "qualify",
        transition_qualify,
        {"qualify_followup": "qualify_followup", "qualify": "qualify", "close": "close"},
    )
    g.add_conditional_edges(
        "qualify_followup",
        transition_qualify_followup,
        {"consent": "consent", "qualify_followup": "qualify_followup", "close": "close"},
    )
    g.add_conditional_edges(
        "consent",
        transition_consent,
        {"next_step": "next_step", "consent": "consent", "close": "close"},
    )
    g.add_conditional_edges(
        "next_step",
        transition_next_step,
        {"close": "close"},
    )
    g.add_conditional_edges(
        "close",
        transition_close,
        {"__end__": END},
    )

    return g.compile(
        checkpointer=MemorySaver(),
        interrupt_after=_INTERRUPT_AFTER,
    )
