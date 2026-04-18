"""Shared data-transfer types for the LLM client layer.

StructuredAgentResponse is the canonical definition of the JSON object that the
dialog LLM (Groq JSON mode) returns for every dialog turn.

NOTE: packages/dialog/dialog/personal_loan/schema.py contains a parallel copy of
StructuredAgentResponse so that the dialog package has zero runtime dependency on
llm_client. These two definitions must stay in sync.  A future chore commit can
make dialog import from here once the dependency direction is reviewed.
"""
from __future__ import annotations

from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field


class ChatMessage(TypedDict):
    """A single message in the chat history passed to the LLM."""
    role: str       # "system" | "user" | "assistant"
    content: str


class StructuredAgentResponse(BaseModel):
    """The JSON object every dialog node expects back from the LLM (Groq JSON mode).

    classified_intent  — the dialog engine's routing signal.
    slots_extracted    — key/value pairs the node should merge into DialogState.slots.
    agent_turn_text    — the agent's next utterance (≤ 30 words per ADR 0002 §5).
    """
    classified_intent: Literal["affirm", "deny", "provide_value", "unclear"]
    slots_extracted: dict[str, Any] = Field(default_factory=dict)
    agent_turn_text: str
