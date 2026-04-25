"""Enriched node functions for the four_wheeler dialog graph.
Delegates to dialog._shared.nodes_base for enriched async logic.
"""
from __future__ import annotations
from dialog._shared.nodes_base import make_nodes
from .prompts import build_messages, get_fallback_text
from .schema import StructuredAgentResponse
from .state import DialogNode, DialogState, SlotSet, TurnRecord

(
    LLMCallable, EligibilityCallable, RAGCallable,
    opener_node, identity_confirm_node, qualify_node,
    qualify_followup_node, consent_node, next_step_node, close_node,
    _call_llm, _append_turns,
) = make_nodes(build_messages, get_fallback_text, StructuredAgentResponse)

__all__ = [
    "LLMCallable", "EligibilityCallable", "RAGCallable",
    "opener_node", "identity_confirm_node", "qualify_node",
    "qualify_followup_node", "consent_node", "next_step_node", "close_node",
    "_call_llm", "_append_turns",
]
