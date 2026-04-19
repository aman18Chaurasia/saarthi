"""Structured response schema returned by the dialog LLM (Groq JSON mode).

The LLM is instructed to return exactly this shape for every dialog node.
If JSON parsing or validation fails, the node treats it as classified_intent='unclear'.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class StructuredAgentResponse(BaseModel):
    classified_intent: Literal["affirm", "deny", "provide_value", "unclear"]
    slots_extracted: dict[str, Any] = Field(default_factory=dict)
    agent_turn_text: str

    # JSON schema string embedded in the system prompt
    JSON_SCHEMA: str = (
        '{\n'
        '  "classified_intent": "affirm" | "deny" | "provide_value" | "unclear",\n'
        '  "slots_extracted": { "<slot_name>": <value> },\n'
        '  "agent_turn_text": "<agent response, max 30 words>"\n'
        '}'
    )
