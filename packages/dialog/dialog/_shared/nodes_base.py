"""Shared enriched node implementations for all 10 SAARTHI dialog products.

All products except personal_loan previously used a stripped-down copy of
home_loan/nodes.py with no history, no sentiment, no RAG.  This module provides
the enriched equivalents.  Each product's nodes.py just imports from here and
supplies its own build_messages / get_fallback_text callables.

Usage in each product's nodes.py:
    from .prompts import build_messages, get_fallback_text
    from .schema import StructuredAgentResponse
    from .state import DialogNode, DialogState, SlotSet, TurnRecord
    from dialog._shared.nodes_base import make_nodes

    (
        LLMCallable, EligibilityCallable, RAGCallable,
        opener_node, identity_confirm_node, qualify_node,
        qualify_followup_node, consent_node, next_step_node, close_node,
        _call_llm, _append_turns,
    ) = make_nodes(build_messages, get_fallback_text, StructuredAgentResponse)
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Callable, Awaitable
import importlib.util

from pydantic import ValidationError

from dialog.slot_requirements import determine_outcome, followup_slot_captured, primary_slot_captured

logger = logging.getLogger(__name__)


# ── Load optional Tier-1 modules (memory + sentiment) ──────────────────────────

def _load_module(name: str, file_path: Path):
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


_base_path = Path(__file__).parents[1]  # packages/dialog/dialog/
_memory_mod = _load_module("memory", _base_path / "memory_manager.py")
_sentiment_mod = _load_module("sentiment", _base_path.parents[1] / "voice" / "sentiment_analyzer.py")

ConversationMemory = _memory_mod.ConversationMemory if _memory_mod else None
SentimentAnalyzer = _sentiment_mod.SentimentAnalyzer if _sentiment_mod else None

_sentiment_analyzer = SentimentAnalyzer() if SentimentAnalyzer else None
_conversation_memories: dict[str, Any] = {}


def _get_memory(call_id: str):
    if not ConversationMemory:
        return None
    if call_id not in _conversation_memories:
        _conversation_memories[call_id] = ConversationMemory()
    return _conversation_memories[call_id]


# ── Internal helpers (product-independent) ────────────────────────────────────

def _update_slots(SlotSetClass, current, extracted: dict[str, Any]):
    valid_fields = SlotSetClass.model_fields
    safe = {k: v for k, v in extracted.items() if k in valid_fields}
    return current.model_copy(update=safe) if safe else current


def _was_useful(resp, updated_slots, node_name: str, SlotSetClass) -> bool:
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
    return True


def _append_turns_impl(state, TurnRecordClass, node_name: str, agent_text: str, *, include_customer: bool = True):
    history = list(state.history)
    ti = state.turn_index
    if include_customer and state.asr_text:
        history.append(TurnRecordClass(
            speaker="customer",
            text=state.asr_text,
            node_name=node_name,
            turn_index=ti,
        ))
        ti += 1
    history.append(TurnRecordClass(
        speaker="agent",
        text=agent_text,
        node_name=node_name,
        turn_index=ti,
    ))
    return history, ti + 1


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


def _consent_reprompt(state) -> str:
    name = getattr(state, "customer_name", "customer")
    return (
        f"{name} ji, main sensitive number note nahi kar sakta jab tak aap clear permission na dein. "
        "Kya aap details record karne ki consent dete hain?"
    )


# ── Factory that creates product-specific node functions ──────────────────────

def make_nodes(build_messages_fn, get_fallback_text_fn, StructuredAgentResponseClass):
    """Return a tuple of enriched node callables bound to product-specific prompt fns."""

    # Type aliases
    LLMCallable = Callable[[list[dict[str, str]], str, str], Awaitable[StructuredAgentResponseClass]]
    EligibilityCallable = Callable[[str, Any, Any], Awaitable[Any]]
    RAGCallable = Callable[[str, str | None, int], Awaitable[str]]

    async def _build_messages_enriched(state, node_name: str, rag_fn=None):
        """Build messages with full Tier-1 enrichment: sentiment, memory, RAG, history."""
        sentiment_guidance = ""
        if _sentiment_analyzer and state.asr_text:
            try:
                sentiment = await _sentiment_analyzer.analyze(state.asr_text)
                sentiment_guidance = await _sentiment_analyzer.get_adaptive_response_guidance(sentiment)
            except Exception as e:
                logger.debug(f"Sentiment analysis failed: {e}")

        rag_context = ""
        if rag_fn and state.asr_text:
            try:
                question_words = ["kya", "what", "how", "why", "kitna", "kaun", "kis", "kab",
                                  "क्या", "कितना", "कैसे", "کیا", "کتنا"]
                if any(w in state.asr_text.lower() for w in question_words) or "?" in state.asr_text:
                    rag_context = await rag_fn(query=state.asr_text, product=state.product, top_k=3)
            except Exception as e:
                logger.debug(f"RAG retrieval failed: {e}")

        memory_context = ""
        memory = _get_memory(state.call_id)
        if memory and state.asr_text:
            try:
                memory_context = await memory.retrieve_relevant_context(query=state.asr_text, max_turns=3)
                facts = memory.get_key_facts_summary()
                if facts:
                    memory_context += "\n\n" + facts
            except Exception as e:
                logger.debug(f"Memory retrieval failed: {e}")

        # Build messages; call product's build_messages with enriched kwargs
        import inspect
        sig = inspect.signature(build_messages_fn)
        params = sig.parameters
        kwargs: dict[str, Any] = dict(
            agent_name=state.agent_name,
            lender_name=state.lender_name,
            customer_name=state.customer_name,
            node_name=node_name,
            asr_text=state.asr_text,
        )
        if "history" in params:
            kwargs["history"] = state.history
        if "retry_count" in params:
            kwargs["retry_count"] = state.retry_count
        if "sentiment_guidance" in params:
            kwargs["sentiment_guidance"] = sentiment_guidance
        if "memory_context" in params:
            kwargs["memory_context"] = memory_context
        if "rag_context" in params:
            kwargs["rag_context"] = rag_context
        return build_messages_fn(**kwargs)

    async def _call_llm(llm_fn, state, node_name: str, rag_fn=None):
        messages = await _build_messages_enriched(state, node_name, rag_fn)
        try:
            resp = await llm_fn(messages, node_name, state.asr_text)
            if isinstance(resp, dict):
                return StructuredAgentResponseClass.model_validate(resp)
            return resp
        except (json.JSONDecodeError, ValidationError, KeyError, TypeError, ValueError):
            return StructuredAgentResponseClass(
                classified_intent="unclear",
                slots_extracted={},
                agent_turn_text=get_fallback_text_fn(
                    node_name, state.agent_name, state.lender_name, state.customer_name
                ),
            )

    def _append_turns(state, node_name: str, agent_text: str, *, include_customer: bool = True):
        from .nodes_base import _append_turns_impl  # self-ref is fine
        # We need TurnRecord from the product's state module — import dynamically
        # Since each product imports its own state, we pick it from state.__class__.__module__
        history = list(state.history)
        ti = state.turn_index
        if include_customer and state.asr_text:
            # Build a dict-compatible record; history accepts both Pydantic and dicts
            history.append({"speaker": "customer", "text": state.asr_text,
                             "node_name": node_name, "turn_index": ti})
            ti += 1
        history.append({"speaker": "agent", "text": agent_text,
                        "node_name": node_name, "turn_index": ti})
        return history, ti + 1

    # ── Node functions ────────────────────────────────────────────────────────

    async def opener_node(state, llm_fn, rag_fn=None):
        resp = await _call_llm(llm_fn, state, "opener", rag_fn)
        history, ti = _append_turns(state, "opener", resp.agent_turn_text, include_customer=False)
        return state.model_copy(update={
            "current_node": "opener", "history": history,
            "turn_index": ti, "retry_count": 0,
        })

    async def identity_confirm_node(state, llm_fn, rag_fn=None):
        memory = _get_memory(state.call_id)
        if memory and state.asr_text:
            try:
                await memory.add_turn("customer", state.asr_text, "identity_confirm", state.turn_index)
            except Exception:
                pass
        resp = await _call_llm(llm_fn, state, "identity_confirm", rag_fn)
        new_slots = _update_slots(state.slots.__class__, state.slots, resp.slots_extracted)
        useful = _was_useful(resp, new_slots, "identity_confirm", state.slots.__class__)
        history, ti = _append_turns(state, "identity_confirm", resp.agent_turn_text)
        if memory:
            try:
                await memory.add_turn("agent", resp.agent_turn_text, "identity_confirm", ti - 1)
            except Exception:
                pass
        return state.model_copy(update={
            "current_node": "identity_confirm", "history": history, "slots": new_slots,
            "retry_count": 0 if useful else state.retry_count + 1, "turn_index": ti,
        })

    async def qualify_node(state, llm_fn, rag_fn=None):
        memory = _get_memory(state.call_id)
        if memory and state.asr_text:
            try:
                await memory.add_turn("customer", state.asr_text, "qualify", state.turn_index)
            except Exception:
                pass
        resp = await _call_llm(llm_fn, state, "qualify", rag_fn)
        new_slots = _update_slots(state.slots.__class__, state.slots, resp.slots_extracted)
        useful = _was_useful(resp, new_slots, "qualify", state.slots.__class__)
        history, ti = _append_turns(state, "qualify", resp.agent_turn_text)
        if memory:
            try:
                await memory.add_turn("agent", resp.agent_turn_text, "qualify", ti - 1)
            except Exception:
                pass
        return state.model_copy(update={
            "current_node": "qualify", "history": history, "slots": new_slots,
            "retry_count": 0 if useful else state.retry_count + 1, "turn_index": ti,
        })

    async def qualify_followup_node(state, llm_fn, eligibility_fn=None, rag_fn=None):
        memory = _get_memory(state.call_id)
        if memory and state.asr_text:
            try:
                await memory.add_turn("customer", state.asr_text, "qualify_followup", state.turn_index)
            except Exception:
                pass
        resp = await _call_llm(llm_fn, state, "qualify_followup", rag_fn)
        new_slots = _update_slots(state.slots.__class__, state.slots, resp.slots_extracted)
        useful = _was_useful(resp, new_slots, "qualify_followup", state.slots.__class__)

        if eligibility_fn and getattr(new_slots, "monthly_income_inr", None) is not None:
            try:
                income = new_slots.monthly_income_inr
                revenue = getattr(new_slots, "monthly_revenue_inr", None)
                elig_result = await eligibility_fn(state.product, income, revenue)
                if not elig_result.eligible:
                    new_slots = new_slots.model_copy(update={"outcome": "not_qualified"})
            except Exception as e:
                logger.warning(f"Eligibility check error: {e}. Continuing.")

        history, ti = _append_turns(state, "qualify_followup", resp.agent_turn_text)
        if memory:
            try:
                await memory.add_turn("agent", resp.agent_turn_text, "qualify_followup", ti - 1)
            except Exception:
                pass
        return state.model_copy(update={
            "current_node": "qualify_followup", "history": history, "slots": new_slots,
            "retry_count": 0 if useful else state.retry_count + 1, "turn_index": ti,
        })

    async def consent_node(state, llm_fn, rag_fn=None):
        memory = _get_memory(state.call_id)
        if memory and state.asr_text:
            try:
                await memory.add_turn("customer", state.asr_text, "consent", state.turn_index)
            except Exception:
                pass
        resp = await _call_llm(llm_fn, state, "consent", rag_fn)
        new_slots = _update_slots(state.slots.__class__, state.slots, resp.slots_extracted)
        agent_text = resp.agent_turn_text
        if new_slots.consent_given is True and _sensitive_detail_without_consent(state.asr_text):
            new_slots = state.slots.model_copy(update={"consent_given": None})
            agent_text = _consent_reprompt(state)
        useful = _was_useful(resp, new_slots, "consent", state.slots.__class__)
        history, ti = _append_turns(state, "consent", agent_text)
        if memory:
            try:
                await memory.add_turn("agent", agent_text, "consent", ti - 1)
            except Exception:
                pass
        return state.model_copy(update={
            "current_node": "consent", "history": history, "slots": new_slots,
            "retry_count": 0 if useful else state.retry_count + 1, "turn_index": ti,
        })

    async def next_step_node(state, llm_fn, rag_fn=None):
        resp = await _call_llm(llm_fn, state, "next_step", rag_fn)
        history, ti = _append_turns(state, "next_step", resp.agent_turn_text, include_customer=False)
        return state.model_copy(update={
            "current_node": "next_step", "history": history, "retry_count": 0, "turn_index": ti,
        })

    async def close_node(state, llm_fn, rag_fn=None):
        resp = await _call_llm(llm_fn, state, "close", rag_fn)
        outcome = determine_outcome(state.slots, product=state.product)
        new_slots = state.slots.model_copy(update={"outcome": outcome})
        history, ti = _append_turns(state, "close", resp.agent_turn_text, include_customer=False)
        return state.model_copy(update={
            "current_node": "close", "history": history, "slots": new_slots, "turn_index": ti,
        })

    return (
        LLMCallable, EligibilityCallable, RAGCallable,
        opener_node, identity_confirm_node, qualify_node,
        qualify_followup_node, consent_node, next_step_node, close_node,
        _call_llm, _append_turns,
    )
