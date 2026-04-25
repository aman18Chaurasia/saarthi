"""LangGraph processor tests with a mocked graph."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from pipecat.frames.frames import TextFrame, TranscriptionFrame
from pipecat.tests.utils import run_test

from dialog.personal_loan.state import SlotSet, TurnRecord
from apps.api.frame_processors.langgraph_processor import LangGraphProcessor, _extract_agent_text
from apps.api.frames import LatencyFrame


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
    app.aget_state = AsyncMock(
        return_value=SimpleNamespace(
            values={"current_node": "qualify", "product": "personal_loan"},
            next=(),
        )
    )
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
    app.aget_state = AsyncMock(
        return_value=SimpleNamespace(
            values={"current_node": "qualify", "product": "personal_loan"},
            next=(),
        )
    )
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


@pytest.mark.asyncio
async def test_closed_call_product_question_gets_rag_answer() -> None:
    async def fake_rag(query: str, product: str | None, top_k: int) -> str:
        assert product == "personal_loan"
        assert top_k == 2
        return (
            "## Key Features - Loan Amount: Rs 50,000 to Rs 10,00,000 "
            "- Interest Rate: 10.5% - 18% p.a. - Processing Fee: 2% of loan amount "
            "## Required Documents - PAN Card - Aadhaar Card - Last 3 months salary slips"
        )

    app = MagicMock()
    app.aget_state = AsyncMock(
        return_value=SimpleNamespace(
            values={"current_node": "close", "product": "personal_loan", "turn_index": 5},
            next=(),
        )
    )
    app.update_state = MagicMock()
    app.ainvoke = AsyncMock()
    processor = LangGraphProcessor(
        app=app,
        config={"configurable": {"thread_id": "test"}},
        closed_rag_fn=fake_rag,
    )

    transcription = TranscriptionFrame(
        text="processing fee kitni hai?", user_id="u", timestamp="0", finalized=True
    )
    down, _up = await run_test(processor, frames_to_send=[transcription])

    text_frames = [f for f in down if type(f) is TextFrame]
    assert len(text_frames) == 1
    assert "processing fee: 2% of loan amount" in text_frames[0].text
    assert text_frames[0].metadata["node_name"] == "rag_after_close"
    app.update_state.assert_not_called()
    app.ainvoke.assert_not_called()


@pytest.mark.asyncio
async def test_closed_call_non_question_stays_closed() -> None:
    app = MagicMock()
    app.aget_state = AsyncMock(
        return_value=SimpleNamespace(
            values={"current_node": "close", "product": "personal_loan"},
            next=(),
        )
    )
    app.update_state = MagicMock()
    app.ainvoke = AsyncMock()
    processor = LangGraphProcessor(app=app, config={"configurable": {"thread_id": "test"}})

    transcription = TranscriptionFrame(
        text="thank you", user_id="u", timestamp="0", finalized=True
    )
    down, _up = await run_test(processor, frames_to_send=[transcription])

    text_frames = [f for f in down if type(f) is TextFrame]
    assert text_frames == []
    app.update_state.assert_not_called()
    app.ainvoke.assert_not_called()


@pytest.mark.asyncio
async def test_processor_auto_advances_next_step_but_not_close() -> None:
    app = MagicMock()
    app.aget_state = AsyncMock(
        side_effect=[
            SimpleNamespace(
                values={"current_node": "consent", "product": "personal_loan"},
                next=(),
            ),
            SimpleNamespace(
                values={"current_node": "consent", "product": "personal_loan"},
                next=("next_step",),
            ),
            SimpleNamespace(
                values={"current_node": "next_step", "product": "personal_loan"},
                next=("close",),
            ),
        ]
    )
    app.update_state = MagicMock()
    app.ainvoke = AsyncMock(
        side_effect=[
            _make_state("Consent recorded."),
            {
                "current_node": "next_step",
                "slots": SlotSet(),
                "history": [
                    TurnRecord(
                        speaker="agent",
                        text="Offer 24 ghante mein aayega.",
                        node_name="next_step",
                        turn_index=2,
                    )
                ],
                "retry_count": 0,
                "error_count": 0,
                "turn_index": 3,
                "asr_text": "haan",
            },
        ]
    )
    processor = LangGraphProcessor(app=app, config={"configurable": {"thread_id": "test"}})

    transcription = TranscriptionFrame(text="haan", user_id="u", timestamp="0", finalized=True)
    down, _up = await run_test(processor, frames_to_send=[transcription])

    text_frames = [f.text for f in down if type(f) is TextFrame]
    assert text_frames == [
        "Consent recorded.",
        "Offer 24 ghante mein aayega.",
    ]

    latency_frames = [f for f in down if isinstance(f, LatencyFrame)]
    assert len(latency_frames) == 2
    assert app.ainvoke.await_count == 2


@pytest.mark.asyncio
async def test_pending_close_product_question_gets_answer_without_closing() -> None:
    async def fake_rag(query: str, product: str | None, top_k: int) -> str:
        return "## Key Features - Minimum Monthly Income: Rs 25,000 - Interest Rate: 10.5%"

    app = MagicMock()
    app.aget_state = AsyncMock(
        return_value=SimpleNamespace(
            values={"current_node": "next_step", "product": "personal_loan", "turn_index": 6},
            next=("close",),
        )
    )
    app.update_state = MagicMock()
    app.ainvoke = AsyncMock()
    processor = LangGraphProcessor(
        app=app,
        config={"configurable": {"thread_id": "test"}},
        closed_rag_fn=fake_rag,
    )

    transcription = TranscriptionFrame(
        text="eligibility kya hai iski?", user_id="u", timestamp="0", finalized=True
    )
    down, _up = await run_test(processor, frames_to_send=[transcription])

    text_frames = [f for f in down if type(f) is TextFrame]
    assert len(text_frames) == 1
    assert "minimum monthly income" in text_frames[0].text.lower()
    app.update_state.assert_not_called()
    app.ainvoke.assert_not_called()
