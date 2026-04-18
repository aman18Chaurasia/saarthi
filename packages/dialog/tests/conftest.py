"""Shared fixtures for dialog tests.

mock_llm_for(scenario)  — builds a deterministic LLM callable from a scenario dict.
sequence_llm_for(seqs)  — per-node response list (pops in order; last repeats).
ConversationRunner      — drives the compiled graph through interrupt/resume cycles.
make_state()            — convenience factory for a minimal DialogState.
"""
from __future__ import annotations

import uuid
from collections.abc import Awaitable
from typing import Any, Callable

import pytest

from dialog.personal_loan.graph import build_graph
from dialog.personal_loan.schema import StructuredAgentResponse
from dialog.personal_loan.state import DialogState

# ── Response builders ─────────────────────────────────────────────────────────

def _resp(
    intent: str = "unclear",
    slots: dict[str, Any] | None = None,
    text: str = "Mock agent turn.",
) -> StructuredAgentResponse:
    return StructuredAgentResponse(
        classified_intent=intent,  # type: ignore[arg-type]
        slots_extracted=slots or {},
        agent_turn_text=text,
    )


# ── Deterministic mock keyed by (node_name, asr_text) ────────────────────────

def mock_llm_for(
    responses: dict[str | tuple[str, str], StructuredAgentResponse],
) -> Callable[..., Awaitable[StructuredAgentResponse]]:
    """Return an async LLM callable driven by a pre-loaded response dict.

    Keys can be:
      - A node name string (matches any asr_text for that node)
      - A (node_name, asr_text) tuple (exact match; takes priority)
    """
    async def _llm(
        messages: list[dict[str, str]],
        node_name: str,
        asr_text: str,
    ) -> StructuredAgentResponse:
        exact = (node_name, asr_text)
        if exact in responses:
            return responses[exact]
        if node_name in responses:
            return responses[node_name]
        raise KeyError(
            f"No mock response for node={node_name!r}, asr_text={asr_text!r}. "
            f"Available keys: {list(responses.keys())}"
        )

    return _llm


# ── Sequence mock for retry scenarios ────────────────────���───────────────────

def sequence_llm_for(
    sequences: dict[str, list[StructuredAgentResponse]],
) -> Callable[..., Awaitable[StructuredAgentResponse]]:
    """Return an async LLM callable that iterates through a response list per node.

    On each call for a given node, returns the next item in the list.
    Repeats the last item once the list is exhausted.
    """
    cursors: dict[str, int] = {}

    async def _llm(
        messages: list[dict[str, str]],
        node_name: str,
        asr_text: str,
    ) -> StructuredAgentResponse:
        if node_name not in sequences:
            raise KeyError(f"No mock sequence for node={node_name!r}")
        seq = sequences[node_name]
        i = cursors.get(node_name, 0)
        resp = seq[min(i, len(seq) - 1)]
        cursors[node_name] = i + 1
        return resp

    return _llm


# ── ConversationRunner — drives interrupt/resume cycles ───────────────────────

class ConversationRunner:
    """Wraps a compiled LangGraph app to drive multi-turn conversations in tests.

    Must be constructed with the async factory::

        runner = await ConversationRunner.create(app, initial_state)
        await runner.say("Haan ji, main hoon")      # identity_confirm
        await runner.say("50000 rupees")             # qualify
        await runner.say("home renovation")          # qualify_followup
        await runner.say("haan, consent deta hoon")  # consent
        await runner.advance()                       # next_step → close
        assert runner.outcome == "qualified"
    """

    def __init__(self, app: Any, cfg: dict[str, Any]) -> None:
        self._app = app
        self._cfg = cfg
        self._state: dict[str, Any] = {}

    @classmethod
    async def create(cls, app: Any, initial_state: DialogState) -> "ConversationRunner":
        """Start the graph (runs opener) and return a ready runner."""
        runner = cls(app, {"configurable": {"thread_id": str(uuid.uuid4())}})
        runner._state = await app.ainvoke(initial_state.model_dump(), runner._cfg)
        return runner

    @property
    def state(self) -> dict[str, Any]:
        return self._state

    @property
    def current_node(self) -> str:
        return str(self._state.get("current_node", ""))

    @property
    def slots(self) -> Any:
        return self._state.get("slots")

    @property
    def outcome(self) -> str | None:
        s = self.slots
        if s is None:
            return None
        return s.outcome if hasattr(s, "outcome") else s.get("outcome")

    @property
    def history(self) -> list[Any]:
        return list(self._state.get("history", []))

    @property
    def retry_count(self) -> int:
        return int(self._state.get("retry_count", 0))

    async def say(self, asr_text: str) -> "ConversationRunner":
        """Inject customer speech, advance one interrupt cycle."""
        self._app.update_state(self._cfg, {"asr_text": asr_text})
        self._state = await self._app.ainvoke(None, self._cfg)
        return self

    async def advance(self) -> "ConversationRunner":
        """Advance without injecting customer input (used for next_step → close → END)."""
        return await self.say("")


# ── Convenience state factory ──────────────────────────────��──────────────────

def make_state(**kwargs: Any) -> DialogState:
    defaults: dict[str, Any] = {
        "call_id": f"test-{uuid.uuid4().hex[:8]}",
        "customer_id": "cust-001",
        "agent_name": "Rohan",
        "lender_name": "TestBank",
        "customer_name": "Priya",
    }
    defaults.update(kwargs)
    return DialogState(**defaults)


# ── Pytest fixtures ──────────────────────────────��────────────────────────────

@pytest.fixture
def state() -> DialogState:
    return make_state()
