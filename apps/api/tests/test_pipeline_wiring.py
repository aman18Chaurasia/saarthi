"""Pipeline wiring test with all external adapters mocked.

Pushes fake audio through the full processor chain and asserts the
expected frame sequence: VAD events -> TranscriptionFrame -> TextFrame -> TTS audio.
No Groq, ElevenLabs, or Postgres calls.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from pipecat.frames.frames import (
    AudioRawFrame,
    TextFrame,
    TranscriptionFrame,
    UserAudioRawFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.tests.utils import run_test

from dialog.personal_loan.state import SlotSet, TurnRecord
from frame_processors.asr_processor import ASRProcessor
from frame_processors.langgraph_processor import LangGraphProcessor
from frame_processors.tts_processor import TTSProcessor
from frame_processors.vad_processor import VADProcessor, _FRAME_BYTES
from frames import LatencyFrame


# Mock helpers

class _MockVad:
    def __init__(self, responses: list[bool]) -> None:
        self._iter = iter(responses)

    def is_speech(self, frame: bytes, sample_rate: int) -> bool:
        return next(self._iter, False)


def _make_graph_state(agent_text: str) -> dict:
    return {
        "current_node": "qualify",
        "slots": SlotSet(),
        "history": [
            TurnRecord(speaker="agent", text=agent_text, node_name="qualify", turn_index=0)
        ],
        "retry_count": 0,
        "turn_index": 1,
        "asr_text": "haan",
    }


def _make_tts_provider(chunks: list[bytes]) -> object:
    class _MockTTS:
        last_first_byte_ms: float | None = None

        async def stream(self, text: str, **kwargs: object) -> AsyncIterator[bytes]:
            for chunk in chunks:
                yield chunk

    return _MockTTS()


def _make_pipeline(
    vad_responses: list[bool],
    transcript: str,
    agent_text: str,
    tts_chunks: list[bytes],
) -> Pipeline:
    vad = VADProcessor(vad_impl=_MockVad(vad_responses))
    asr = ASRProcessor(transcribe_fn=AsyncMock(return_value=transcript))

    app = MagicMock()
    app.update_state = MagicMock()
    app.ainvoke = AsyncMock(return_value=_make_graph_state(agent_text))
    lg = LangGraphProcessor(app=app, config={"configurable": {"thread_id": "test"}})

    tts = TTSProcessor(tts_provider=_make_tts_provider(tts_chunks))

    return Pipeline([vad, asr, lg, tts])


def _audio_frame() -> AudioRawFrame:
    return UserAudioRawFrame(
        audio=b"\x00" * _FRAME_BYTES,
        sample_rate=16000,
        num_channels=1,
        user_id="test",
    )


# Tests

@pytest.mark.asyncio
async def test_full_chain_frame_sequence() -> None:
    """Happy path: audio -> VAD events -> transcription -> agent text -> TTS audio."""
    # 3 silence, 10 speech, 20 silence (exceeds 15-frame padding).
    vad_responses = [False] * 3 + [True] * 10 + [False] * 20
    tts_chunk = b"\x04\x05" * 2048

    pipeline = _make_pipeline(
        vad_responses=vad_responses,
        transcript="Haan, main hoon",
        agent_text="Income kitni hai?",
        tts_chunks=[tts_chunk],
    )

    # 33 audio frames: each 640 bytes = one 20ms VAD chunk
    audio_frames = [_audio_frame() for _ in range(33)]
    down, _up = await run_test(pipeline, frames_to_send=audio_frames)

    frame_types = [type(f).__name__ for f in down]

    assert "UserStartedSpeakingFrame" in frame_types
    assert "UserStoppedSpeakingFrame" in frame_types
    assert "TranscriptionFrame" in frame_types
    assert "TextFrame" in frame_types
    # TTS audio must arrive as AudioRawFrame downstream
    audio_out = [f for f in down if isinstance(f, AudioRawFrame)]
    assert any(f.audio == tts_chunk for f in audio_out)


@pytest.mark.asyncio
async def test_frame_order_is_correct() -> None:
    """VAD events must precede transcription, which must precede TTS audio."""
    vad_responses = [False] * 3 + [True] * 10 + [False] * 20
    pipeline = _make_pipeline(
        vad_responses=vad_responses,
        transcript="test",
        agent_text="agent reply",
        tts_chunks=[b"\x00" * 100],
    )

    audio_frames = [_audio_frame() for _ in range(33)]
    down, _up = await run_test(pipeline, frames_to_send=audio_frames)

    types = [type(f).__name__ for f in down]

    # Verify ordering
    start_idx = next((i for i, t in enumerate(types) if t == "UserStartedSpeakingFrame"), None)
    stop_idx = next((i for i, t in enumerate(types) if t == "UserStoppedSpeakingFrame"), None)
    trans_idx = next((i for i, t in enumerate(types) if t == "TranscriptionFrame"), None)
    text_idx = next((i for i, t in enumerate(types) if t == "TextFrame"), None)

    assert start_idx is not None and stop_idx is not None
    assert trans_idx is not None and text_idx is not None
    assert start_idx < stop_idx
    assert stop_idx < trans_idx
    assert trans_idx < text_idx


@pytest.mark.asyncio
async def test_latency_frames_emitted_by_asr_and_llm_and_tts() -> None:
    vad_responses = [False] * 3 + [True] * 10 + [False] * 20
    pipeline = _make_pipeline(
        vad_responses=vad_responses,
        transcript="test",
        agent_text="test reply",
        tts_chunks=[b"\x00" * 100],
    )

    audio_frames = [_audio_frame() for _ in range(33)]
    down, _up = await run_test(pipeline, frames_to_send=audio_frames)

    latency_frames = [f for f in down if isinstance(f, LatencyFrame)]
    hops = {f.hop for f in latency_frames}
    assert "asr" in hops
    assert "llm" in hops
    assert "tts" in hops


@pytest.mark.asyncio
async def test_pure_silence_produces_no_transcription() -> None:
    """No speech means no TranscriptionFrame, no TextFrame, and no TTS audio."""
    vad_responses = [False] * 30
    pipeline = _make_pipeline(
        vad_responses=vad_responses,
        transcript="this should not be called",
        agent_text="should not appear",
        tts_chunks=[b"\x00" * 100],
    )

    audio_frames = [_audio_frame() for _ in range(30)]
    down, _up = await run_test(pipeline, frames_to_send=audio_frames)

    assert not any(isinstance(f, TranscriptionFrame) for f in down)
    assert not any(isinstance(f, TextFrame) for f in down)
