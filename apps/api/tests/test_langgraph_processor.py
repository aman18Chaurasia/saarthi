"""LangGraph processor tests with a mocked graph."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from pipecat.frames.frames import TextFrame, TranscriptionFrame
from pipecat.tests.utils import run_test

from dialog.personal_loan.state import SlotSet, TurnRecord
from frame_processors.langgraph_processor import LangGraphProcessor, _extract_agent_text
from frames import LatencyFrame


def _make_state(agent_text: str = "Income kitni hai?") -> dict:
    """Return a minimal dialog state dict as returned by ainvoke."""
    return {
        "current_node": "qualify",
        "slots": SlotSet(),
        "history": [
            TurnRecord(speaker="agent", text=agent_text, node_name="qualify", turn_index=0)
        ],
        "retry_count": 0,
        "error_count": 0,
        "turn_index": 1,
        "asr_text": "haan, main hoon",
    }


def _make_processor(agent_text: str = "Income kitni hai?") -> LangGraphProcessor:
    app = MagicMock()
    app.update_state = MagicMock()
    app.ainvoke = AsyncMock(return_value=_make_state(agent_text))
    config = {"configurable": {"thread_id": "test-call"}}
    return LangGraphProcessor(app=app, config=config)


# _extract_agent_text unit tests

def test_extract_agent_text_from_pydantic_history() -> None:
    state = _make_state("Namaste!")
    assert _extract_agent_text(state) == "Namaste!"


def test_extract_agent_text_from_dict_history() -> None:
    state = {
        "history": [
            {"speaker": "customer", "text": "Haan", "node_name": "opener", "turn_index": 0},
            {"speaker": "agent", "text": "Great, income?", "node_name": "qualify", "turn_index": 1},
        ]
    }
    assert _extract_agent_text(state) == "Great, income?"


def test_extract_agent_text_empty_history() -> None:
    assert _extract_agent_text({"history": []}) == ""


def test_extract_agent_text_only_customer_turns() -> None:
    state = {"history": [TurnRecord(speaker="customer", text="hi", node_name="opener", turn_index=0)]}
    assert _extract_agent_text(state) == ""


# Processor integration tests using pipecat.tests.utils.run_test

@pytest.mark.asyncio
async def test_transcription_frame_produces_text_frame() -> None:
    processor = _make_processor("Income kitni hai?")
    transcription = TranscriptionFrame(
        text="Haan, main Priya hoon", user_id="user1", timestamp="0", finalized=True
    )
    down, _up = await run_test(processor, frames_to_send=[transcription])

    text_frames = [f for f in down if type(f) is TextFrame]
    assert len(text_frames) == 1
    assert text_frames[0].text == "Income kitni hai?"


@pytest.mark.asyncio
async def test_transcription_frame_produces_latency_frame() -> None:
    processor = _make_processor("Income kitni hai?")
    transcription = TranscriptionFrame(text="test", user_id="u", timestamp="0", finalized=True)
    down, _up = await run_test(processor, frames_to_send=[transcription])

    latency_frames = [f for f in down if isinstance(f, LatencyFrame)]
    assert len(latency_frames) == 1
    assert latency_frames[0].hop == "llm"
    assert latency_frames[0].duration_ms >= 0.0


@pytest.mark.asyncio
async def test_text_frame_comes_before_latency_frame() -> None:
    processor = _make_processor("Response text")
    transcription = TranscriptionFrame(text="test", user_id="u", timestamp="0", finalized=True)
    down, _up = await run_test(processor, frames_to_send=[transcription])

    relevant = [f for f in down if type(f) is TextFrame or isinstance(f, LatencyFrame)]
    assert len(relevant) == 2
    assert isinstance(relevant[0], TextFrame)
    assert isinstance(relevant[1], LatencyFrame)


@pytest.mark.asyncio
async def test_update_state_called_with_asr_text() -> None:
    app = MagicMock()
    app.update_state = MagicMock()
    app.ainvoke = AsyncMock(return_value=_make_state("test"))
    config = {"configurable": {"thread_id": "test"}}
    processor = LangGraphProcessor(app=app, config=config)

    transcription = TranscriptionFrame(text="50000 rupees", user_id="u", timestamp="0")
    await run_test(processor, frames_to_send=[transcription])

    app.update_state.assert_called_once_with(config, {"asr_text": "50000 rupees"})


@pytest.mark.asyncio
async def test_non_transcription_frames_pass_through() -> None:
    processor = _make_processor()
    text_in = TextFrame(text="unrelated text")

    down, _up = await run_test(processor, frames_to_send=[text_in])

    # LangGraph processor should not touch non-transcription frames
    passed = [f for f in down if type(f) is TextFrame]
    assert any(f.text == "unrelated text" for f in passed)
