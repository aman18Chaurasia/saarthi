"""LangGraph frame processor: drives the personal-loan dialog state machine.

On TranscriptionFrame:
  1. update_state(config, {"asr_text": text})
  2. ainvoke(None, config) -> new state dict
  3. Extract last agent TurnRecord from history
  4. Emit TextFrame(text=agent_turn_text) + LatencyFrame(hop="llm")
"""
from __future__ import annotations

import time
from typing import Any

from pipecat.frames.frames import Frame, TextFrame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from frames import LatencyFrame


def _extract_agent_text(state: dict[str, Any]) -> str:
    """Return the last agent utterance from the state history."""
    history = state.get("history", [])
    for turn in reversed(list(history)):
        # Supports both Pydantic model instances and plain dicts
        if hasattr(turn, "speaker"):
            if turn.speaker == "agent":
                return str(turn.text)
        elif isinstance(turn, dict) and turn.get("speaker") == "agent":
            return str(turn.get("text", ""))
    return ""


class LangGraphProcessor(FrameProcessor):
    """Manages one call's dialog graph.  Expects the graph to already have
    been started (opener invoked) before the first TranscriptionFrame arrives.

    Args:
        app:    Compiled LangGraph StateGraph (from build_graph()).
        config: {"configurable": {"thread_id": call_id}} for MemorySaver.
    """

    def __init__(self, app: Any, config: dict[str, Any]) -> None:
        super().__init__()
        self._app = app
        self._config = config

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)

        if not isinstance(frame, TranscriptionFrame):
            await self.push_frame(frame, direction)
            return

        asr_text = frame.text
        t0 = time.perf_counter_ns()

        # Inject customer utterance and advance the dialog graph
        self._app.update_state(self._config, {"asr_text": asr_text})
        result: dict[str, Any] = await self._app.ainvoke(None, self._config)

        llm_ms = (time.perf_counter_ns() - t0) / 1_000_000

        agent_text = _extract_agent_text(result)
        if agent_text:
            text_frame = TextFrame(text=agent_text)
            text_frame.metadata["node_name"] = result.get("current_node", "unknown")
            text_frame.metadata["turn_index"] = result.get("turn_index", 0)
            await self.push_frame(frame, direction)
            await self.push_frame(text_frame, direction)
            await self.push_frame(LatencyFrame(hop="llm", duration_ms=llm_ms), direction)
        else:
            # Forward original transcription so downstream processors aren't stuck
            await self.push_frame(frame, direction)
