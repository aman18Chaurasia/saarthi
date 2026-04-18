"""VAD processor tests using a mock webrtcvad.Vad."""
from __future__ import annotations

import pytest
from pipecat.frames.frames import (
    AudioRawFrame,
    ErrorFrame,
    UserAudioRawFrame,
)
from pipecat.tests.utils import run_test

from frame_processors.vad_processor import VADProcessor, _FRAME_BYTES

# 16-bit silence: all zeros
_SILENCE = b"\x00" * _FRAME_BYTES
_SPEECH = b"\x7f\x01" * (_FRAME_BYTES // 2)  # non-zero to look like speech


class _MockVad:
    """Deterministic is_speech responses from a pre-loaded list."""

    def __init__(self, responses: list[bool]) -> None:
        self._iter = iter(responses)

    def is_speech(self, frame: bytes, sample_rate: int) -> bool:
        return next(self._iter, False)


def _make_audio_frame(data: bytes = _SILENCE) -> AudioRawFrame:
    return UserAudioRawFrame(audio=data, sample_rate=16000, num_channels=1, user_id="test")


# Test: silence -> speech -> silence emits correct boundary events

@pytest.mark.asyncio
async def test_speech_start_emitted_on_first_speech_frame() -> None:
    # 3 silent frames, then 5 speech frames
    vad = _MockVad([False] * 3 + [True] * 5)
    processor = VADProcessor(vad_impl=vad)

    frames = [_make_audio_frame()] * 8
    down, _up = await run_test(processor, frames_to_send=frames, send_end_frame=True)

    types = [type(f).__name__ for f in down]
    assert "UserStartedSpeakingFrame" in types


@pytest.mark.asyncio
async def test_speech_stop_emitted_after_silence_padding() -> None:
    # 5 speech frames, then 15+ silence frames (default padding = 15 frames for 300ms)
    speech = [True] * 5
    silence = [False] * 20
    vad = _MockVad(speech + silence)
    processor = VADProcessor(vad_impl=vad)

    frames = [_make_audio_frame()] * 25
    down, _up = await run_test(processor, frames_to_send=frames, send_end_frame=True)

    types = [type(f).__name__ for f in down]
    assert "UserStartedSpeakingFrame" in types
    assert "UserStoppedSpeakingFrame" in types
    # Start must come before stop
    start_idx = next(i for i, t in enumerate(types) if t == "UserStartedSpeakingFrame")
    stop_idx = next(i for i, t in enumerate(types) if t == "UserStoppedSpeakingFrame")
    assert start_idx < stop_idx


@pytest.mark.asyncio
async def test_no_events_emitted_on_pure_silence() -> None:
    vad = _MockVad([False] * 30)
    processor = VADProcessor(vad_impl=vad)

    frames = [_make_audio_frame()] * 30
    down, _up = await run_test(processor, frames_to_send=frames, send_end_frame=True)

    types = [type(f).__name__ for f in down]
    assert "UserStartedSpeakingFrame" not in types
    assert "UserStoppedSpeakingFrame" not in types


@pytest.mark.asyncio
async def test_audio_frames_always_forwarded_downstream() -> None:
    vad = _MockVad([True] * 10)
    processor = VADProcessor(vad_impl=vad)

    frames = [_make_audio_frame()] * 10
    down, _up = await run_test(processor, frames_to_send=frames, send_end_frame=True)

    audio_frames = [f for f in down if isinstance(f, AudioRawFrame)]
    assert len(audio_frames) == 10


@pytest.mark.asyncio
async def test_wrong_sample_rate_raises_value_error() -> None:
    vad = _MockVad([False])
    processor = VADProcessor(vad_impl=vad)

    bad_frame = UserAudioRawFrame(
        audio=b"\x00" * 640, sample_rate=8000, num_channels=1, user_id="test"
    )

    _down, up = await run_test(processor, frames_to_send=[bad_frame], send_end_frame=True)

    errors = [f for f in up if isinstance(f, ErrorFrame)]
    assert len(errors) == 1
    assert "16000 Hz" in errors[0].error


@pytest.mark.asyncio
async def test_non_mono_audio_raises_error_frame() -> None:
    vad = _MockVad([False])
    processor = VADProcessor(vad_impl=vad)

    bad_frame = UserAudioRawFrame(
        audio=b"\x00" * 640, sample_rate=16000, num_channels=2, user_id="test"
    )

    _down, up = await run_test(processor, frames_to_send=[bad_frame], send_end_frame=True)

    errors = [f for f in up if isinstance(f, ErrorFrame)]
    assert len(errors) == 1
    assert "mono audio" in errors[0].error


@pytest.mark.asyncio
async def test_incomplete_chunk_buffered_until_full_frame() -> None:
    """Send a 320-byte half-frame; VAD must not fire until 640 bytes accumulated."""
    call_count = [0]

    class CountingVad:
        def is_speech(self, frame: bytes, sample_rate: int) -> bool:
            call_count[0] += 1
            return True

    processor = VADProcessor(vad_impl=CountingVad())
    half_frame = UserAudioRawFrame(
        audio=b"\x00" * 320, sample_rate=16000, num_channels=1, user_id="test"
    )

    # Single half-frame: VAD should not be called (not enough bytes yet)
    down, _up = await run_test(processor, frames_to_send=[half_frame], send_end_frame=True)
    assert call_count[0] == 0, "VAD called before full 640-byte frame accumulated"

    # Two half-frames: exactly one 640-byte chunk means VAD is called once.
    call_count[0] = 0
    down, _up = await run_test(
        VADProcessor(vad_impl=CountingVad()),
        frames_to_send=[half_frame, half_frame],
        send_end_frame=True,
    )
    assert call_count[0] == 1
