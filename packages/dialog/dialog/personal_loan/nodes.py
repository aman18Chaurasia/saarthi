"""Async node functions for the personal loan dialog graph.

Each node:
  - Receives DialogState (immutable — do NOT mutate in place).
  - Calls the injected LLM callable once with Groq JSON-mode messages.
  - Returns state.model_copy(update={...}) with updated slots, history, counters.
  - On LLM failure / JSON parse error: falls back to classified_intent='unclear'
    and increments retry_count.

The LLM callable is injected at graph-build time (see graph.py) so tests can
substitute a mock without touching any network.

TIER 1 ENHANCEMENTS:
- Conversation memory with semantic retrieval
- Sentiment analysis for adaptive responses
- Smart retry with dynamic rephrasing
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable, Awaitable
from pathlib import Path
import importlib.util

from pydantic import ValidationError

from dialog.slot_requirements import determine_outcome, followup_slot_captured, primary_slot_captured

from .prompts import build_messages, get_fallback_text
from .schema import StructuredAgentResponse
from .state import DialogNode, DialogState, SlotSet, TurnRecord

# ── Tier 1: Load enhanced modules ─────────────────────────────────────────────
def _load_module(name: str, file_path: Path):
    """Dynamically load a module from file path."""
    try:
        if not file_path.exists():
            return None
        spec = importlib.util.spec_from_file_location(name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    except Exception:
        return None

# Try to load Tier 1 modules
# Path: packages/dialog/dialog/personal_loan/nodes.py
# Target: packages/dialog/dialog/memory_manager.py
_base_path = Path(__file__).parents[1]  # Go up to dialog/
_memory_mod = _load_module('memory', _base_path / 'memory_manager.py')
# Target: packages/voice/sentiment_analyzer.py
_sentiment_mod = _load_module('sentiment', _base_path.parents[1] / 'voice' / 'sentiment_analyzer.py')

# Initialize if available
if _memory_mod:
    ConversationMemory = _memory_mod.ConversationMemory
    _conversation_memories: dict[str, Any] = {}
else:
    ConversationMemory = None
    _conversation_memories = {}

if _sentiment_mod:
    SentimentAnalyzer = _sentiment_mod.SentimentAnalyzer
    _sentiment_analyzer = SentimentAnalyzer()
else:
    SentimentAnalyzer = None
    _sentiment_analyzer = None

# Type alias for the injected LLM callable
LLMCallable = Callable[
    [list[dict[str, str]], str, str],   # (messages, node_name, asr_text)
    Awaitable[StructuredAgentResponse],
]

# Phase 2: Type hints for injectable eligibility and RAG functions
EligibilityCallable = Callable[[str, int | None, int | None], Awaitable[Any]]  # product, income, revenue -> EligibilityResult
RAGCallable = Callable[[str, str | None, int], Awaitable[str]]  # query, product, top_k -> context string

logger = logging.getLogger(__name__)


# ── Tier 1: Memory & Sentiment helpers ───────────────────────────────────────

def _get_memory(call_id: str):
    """Get or create conversation memory for this call."""
    if not ConversationMemory:
        return None
    if call_id not in _conversation_memories:
        _conversation_memories[call_id] = ConversationMemory()
    return _conversation_memories[call_id]


# ── Shared helpers ────────────────────────────────────────────────────────────

async def _build_messages(state: DialogState, node_name: str, rag_fn: RAGCallable | None = None) -> list[dict[str, str]]:
    """Build messages with Tier 1 enhancements (memory + sentiment + RAG).

    Falls back gracefully if modules unavailable.
    """
    # Tier 1: Analyze sentiment
    sentiment_guidance = ""
    if _sentiment_analyzer and state.asr_text:
        try:
            sentiment = await _sentiment_analyzer.analyze(state.asr_text)
            sentiment_guidance = await _sentiment_analyzer.get_adaptive_response_guidance(sentiment)
        except Exception as e:
            logger.debug(f"Sentiment analysis failed: {e}")

    # Phase 2: Retrieve RAG context if available
    rag_context = ""
    if rag_fn and state.asr_text:
        try:
            # Detect if user is asking a question (heuristic: contains "kya", "what", "how", "why", etc.)
            question_words = ["kya", "what", "how", "why", "kitna", "kaun", "kis", "kab"]
            is_question = any(word in state.asr_text.lower() for word in question_words)
            
            if is_question:
                rag_context = await rag_fn(
                    query=state.asr_text,
                    product=state.product,
                    top_k=3
                )
        except Exception as e:
            logger.debug(f"RAG retrieval failed: {e}")

    # Tier 1: Retrieve memory context
    memory_context = ""
    memory = _get_memory(state.call_id)
    if memory and state.asr_text:
        try:
            memory_context = await memory.retrieve_relevant_context(
                query=state.asr_text,
                max_turns=3
            )
            facts = memory.get_key_facts_summary()
            if facts:
                memory_context += "\n\n" + facts
        except Exception as e:
            logger.debug(f"Memory retrieval failed: {e}")

    # Build messages (with or without enhancements)
    return build_messages(
        agent_name=state.agent_name,
        lender_name=state.lender_name,
        customer_name=state.customer_name,
        node_name=node_name,
        asr_text=state.asr_text,
        history=state.history,
        retry_count=state.retry_count,
        sentiment_guidance=sentiment_guidance,
        memory_context=memory_context,
        rag_context=rag_context,
    )


async def _call_llm(
    llm_fn: LLMCallable,
    state: DialogState,
    node_name: str,
    rag_fn: RAGCallable | None = None,
) -> StructuredAgentResponse:
    """Call the LLM and return a validated StructuredAgentResponse.

    On any failure returns a fallback 'unclear' response without raising.
    """
    messages = await _build_messages(state, node_name, rag_fn)
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
        return primary_slot_captured(updated_slots)
    if node_name == "qualify_followup":
        return followup_slot_captured(updated_slots)
    if node_name == "consent":
        return updated_slots.consent_given is not None
    # opener, next_step, close — always considered useful (no retries)
    return True


def _update_slots(current: SlotSet, extracted: dict[str, Any]) -> SlotSet:
    """Merge extracted slot values into the current SlotSet, ignoring unknown keys."""
    valid_fields = SlotSet.model_fields
    safe = {k: v for k, v in extracted.items() if k in valid_fields}
    return current.model_copy(update=safe) if safe else current


_SENSITIVE_DETAIL_PATTERN = re.compile(
    r"\b(?:\d[\s-]?){8,}\b|aadhaar|aadhar|pan|otp|cvv|pin|account|number|mobile|phone",
    re.IGNORECASE,
)
_DENY_CONSENT_PATTERN = re.compile(
    r"\b(?:no|nahi|nahin|mat|don't|do not|cannot|can't)\b.*\b(?:record|permission|consent|use|number)\b"
    r"|\b(?:record|permission|consent|use|number)\b.*\b(?:nahi|nahin|mat|don't|do not|cannot|can't)\b",
    re.IGNORECASE,
)
_EXPLICIT_CONSENT_PATTERN = re.compile(
    r"\b(?:yes|haan|han|sure|okay|ok|consent|permission|allow|record kar sakte|kar sakte)\b",
    re.IGNORECASE,
)


def _sensitive_detail_without_consent(text: str) -> bool:
    if not text:
        return False
    if not _SENSITIVE_DETAIL_PATTERN.search(text):
        return False
    if _DENY_CONSENT_PATTERN.search(text):
        return False
    return not _EXPLICIT_CONSENT_PATTERN.search(text)


def _consent_reprompt(state: DialogState) -> str:
    return (
        f"{state.customer_name} ji, main sensitive number note nahi kar sakta jab tak aap clear permission na dein. "
        "Kya aap details record karne ki consent dete hain?"
    )


# ── Node functions ────────────────────────────────────────────────────────────

async def opener_node(state: DialogState, llm_fn: LLMCallable, rag_fn: RAGCallable | None = None) -> DialogState:
    """Fires at call start — no customer input yet."""
    resp = await _call_llm(llm_fn, state, "opener", rag_fn)
    history, ti = _append_turns(state, "opener", resp.agent_turn_text, include_customer=False)
    return state.model_copy(update={
        "current_node": "opener",
        "history": history,
        "turn_index": ti,
        "retry_count": 0,
    })


async def identity_confirm_node(state: DialogState, llm_fn: LLMCallable, rag_fn: RAGCallable | None = None) -> DialogState:
    # Tier 1: Track customer turn in memory
    memory = _get_memory(state.call_id)
    if memory and state.asr_text:
        try:
            await memory.add_turn("customer", state.asr_text, "identity_confirm", state.turn_index)
        except Exception as e:
            logger.debug(f"Memory tracking failed: {e}")

    resp = await _call_llm(llm_fn, state, "identity_confirm", rag_fn)
    new_slots = _update_slots(state.slots, resp.slots_extracted)
    useful = _was_useful(resp, new_slots, "identity_confirm")
    history, ti = _append_turns(state, "identity_confirm", resp.agent_turn_text)

    # Tier 1: Track agent turn in memory
    if memory:
        try:
            await memory.add_turn("agent", resp.agent_turn_text, "identity_confirm", ti - 1)
        except Exception as e:
            logger.debug(f"Memory tracking failed: {e}")

    return state.model_copy(update={
        "current_node": "identity_confirm",
        "history": history,
        "slots": new_slots,
        "retry_count": 0 if useful else state.retry_count + 1,
        "turn_index": ti,
    })


async def qualify_node(state: DialogState, llm_fn: LLMCallable, rag_fn: RAGCallable | None = None) -> DialogState:
    # Tier 1: Track in memory
    memory = _get_memory(state.call_id)
    if memory and state.asr_text:
        try:
            await memory.add_turn("customer", state.asr_text, "qualify", state.turn_index)
        except Exception:
            pass

    resp = await _call_llm(llm_fn, state, "qualify", rag_fn)
    new_slots = _update_slots(state.slots, resp.slots_extracted)
    useful = _was_useful(resp, new_slots, "qualify")
    history, ti = _append_turns(state, "qualify", resp.agent_turn_text)

    # Track agent turn
    if memory:
        try:
            await memory.add_turn("agent", resp.agent_turn_text, "qualify", ti - 1)
        except Exception:
            pass

    return state.model_copy(update={
        "current_node": "qualify",
        "history": history,
        "slots": new_slots,
        "retry_count": 0 if useful else state.retry_count + 1,
        "turn_index": ti,
    })


async def qualify_followup_node(
    state: DialogState,
    llm_fn: LLMCallable,
    eligibility_fn: EligibilityCallable | None = None,
    rag_fn: RAGCallable | None = None,
) -> DialogState:
    """Qualify followup node with optional eligibility checking and RAG context.

    Phase 2 integration:
    - After extracting slots, checks eligibility if eligibility_fn is provided
    - If ineligible, sets outcome="not_qualified" to route to close node
    - RAG context can be fetched and passed to LLM (future enhancement)

    Tier 1: Memory tracking enabled
    """
    # Tier 1: Track in memory
    memory = _get_memory(state.call_id)
    if memory and state.asr_text:
        try:
            await memory.add_turn("customer", state.asr_text, "qualify_followup", state.turn_index)
        except Exception:
            pass

    resp = await _call_llm(llm_fn, state, "qualify_followup", rag_fn)
    new_slots = _update_slots(state.slots, resp.slots_extracted)
    useful = _was_useful(resp, new_slots, "qualify_followup")

    # Phase 2: Check eligibility if function is provided and we have required data
    if eligibility_fn and new_slots.monthly_income_inr is not None:
        try:
            elig_result = await eligibility_fn(
                state.product,
                new_slots.monthly_income_inr,
                None  # monthly_revenue_inr (only for msme_business)
            )

            if not elig_result.eligible:
                logger.info(f"Eligibility check failed for {state.product}: {elig_result.reasons}")
                # Set outcome to not_qualified to trigger close
                new_slots = new_slots.model_copy(update={"outcome": "not_qualified"})
        except Exception as e:
            logger.warning(f"Eligibility check error: {e}. Continuing without rejection.")

    history, ti = _append_turns(state, "qualify_followup", resp.agent_turn_text)

    # Track agent turn
    if memory:
        try:
            await memory.add_turn("agent", resp.agent_turn_text, "qualify_followup", ti - 1)
        except Exception:
            pass

    return state.model_copy(update={
        "current_node": "qualify_followup",
        "history": history,
        "slots": new_slots,
        "retry_count": 0 if useful else state.retry_count + 1,
        "turn_index": ti,
    })


async def consent_node(state: DialogState, llm_fn: LLMCallable, rag_fn: RAGCallable | None = None) -> DialogState:
    # Tier 1: Track in memory
    memory = _get_memory(state.call_id)
    if memory and state.asr_text:
        try:
            await memory.add_turn("customer", state.asr_text, "consent", state.turn_index)
        except Exception:
            pass

    resp = await _call_llm(llm_fn, state, "consent", rag_fn)
    new_slots = _update_slots(state.slots, resp.slots_extracted)
    agent_text = resp.agent_turn_text
    if new_slots.consent_given is True and _sensitive_detail_without_consent(state.asr_text):
        new_slots = state.slots.model_copy(update={"consent_given": None})
        agent_text = _consent_reprompt(state)
    useful = _was_useful(resp, new_slots, "consent")
    history, ti = _append_turns(state, "consent", agent_text)

    # Track agent turn
    if memory:
        try:
            await memory.add_turn("agent", agent_text, "consent", ti - 1)
        except Exception:
            pass

    return state.model_copy(update={
        "current_node": "consent",
        "history": history,
        "slots": new_slots,
        "retry_count": 0 if useful else state.retry_count + 1,
        "turn_index": ti,
    })


async def next_step_node(state: DialogState, llm_fn: LLMCallable, rag_fn: RAGCallable | None = None) -> DialogState:
    resp = await _call_llm(llm_fn, state, "next_step", rag_fn)
    history, ti = _append_turns(state, "next_step", resp.agent_turn_text, include_customer=False)
    return state.model_copy(update={
        "current_node": "next_step",
        "history": history,
        "retry_count": 0,
        "turn_index": ti,
    })


def _determine_outcome(state: DialogState) -> str:
    return determine_outcome(state.slots, product=state.product)


async def close_node(state: DialogState, llm_fn: LLMCallable, rag_fn: RAGCallable | None = None) -> DialogState:
    resp = await _call_llm(llm_fn, state, "close", rag_fn)
    outcome = _determine_outcome(state)
    new_slots = state.slots.model_copy(update={"outcome": outcome})
    history, ti = _append_turns(state, "close", resp.agent_turn_text, include_customer=False)
    return state.model_copy(update={
        "current_node": "close",
        "history": history,
        "slots": new_slots,
        "turn_index": ti,
    })
