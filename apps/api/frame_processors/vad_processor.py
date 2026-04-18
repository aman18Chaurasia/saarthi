"""VAD frame processor: wraps webrtcvad and emits speech-boundary frames.

Enforces 20 ms / 640-byte frames at 16 kHz (webrtcvad requirement).
Reads VAD_SILENCE_PADDING_MS from env (default 300 ms, ADR 0002 section 8.1).
Accepts an injectable vad_impl for unit testing.
"""
from __future__ import annotations

import os

from pipecat.frames.frames import (
    AudioRawFrame,
    Frame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

# 20 ms at 16 kHz, 16-bit mono = 320 samples * 2 bytes
_SAMPLE_RATE = 16000
_FRAME_MS = 20
_FRAME_BYTES = (_SAMPLE_RATE * _FRAME_MS) // 1000 * 2  # 640 bytes


def _padding_frames() -> int:
    """Number of silent frames that constitute end-of-speech."""
    padding_ms = int(os.environ.get("VAD_SILENCE_PADDING_MS", "300"))
    return max(1, padding_ms // _FRAME_MS)


class VADProcessor(FrameProcessor):
    """Consumes AudioRawFrame chunks, emits UserStarted/StoppedSpeakingFrame.

    All AudioRawFrame chunks are forwarded downstream unchanged so the ASR
    processor can buffer them.  Speech-boundary events are injected in the
    frame stream.

    Args:
        vad_impl: Optional webrtcvad.Vad (or duck-typed mock).  If None,
                  a Vad(3) (highest aggressiveness) is created at init.
    """

    def __init__(self, vad_impl: object | None = None) -> None:
        super().__init__()
        if vad_impl is not None:
            self._vad = vad_impl
        else:
            import webrtcvad as _webrtcvad  # deferred; tests always inject vad_impl
            self._vad = _webrtcvad.Vad(3)
        self._buf = bytearray()
        self._speaking = False
        self._silence_frames = 0
        self._padding_frames = _padding_frames()

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)

        if not isinstance(frame, AudioRawFrame):
            await self.push_frame(frame, direction)
            return

        if frame.sample_rate != _SAMPLE_RATE:
            raise ValueError(
                f"VADProcessor requires {_SAMPLE_RATE} Hz audio; got {frame.sample_rate} Hz"
            )
        if frame.num_channels != 1:
            raise ValueError(f"VADProcessor requires mono audio; got {frame.num_channels} channels")

        # Buffer audio; process in 640-byte (20 ms) chunks
        self._buf.extend(frame.audio)
        while len(self._buf) >= _FRAME_BYTES:
            chunk = bytes(self._buf[:_FRAME_BYTES])
            self._buf = self._buf[_FRAME_BYTES:]
            await self._process_chunk(chunk, direction)

        # Always forward the original frame downstream for ASR buffering
        await self.push_frame(frame, direction)

    async def _process_chunk(self, chunk: bytes, direction: FrameDirection) -> None:
        is_speech = self._vad.is_speech(chunk, _SAMPLE_RATE)

        if is_speech:
            self._silence_frames = 0
            if not self._speaking:
                self._speaking = True
                await self.push_frame(UserStartedSpeakingFrame(), direction)
        else:
            if self._speaking:
                self._silence_frames += 1
                if self._silence_frames >= self._padding_frames:
                    self._speaking = False
                    self._silence_frames = 0
                    await self.push_frame(UserStoppedSpeakingFrame(), direction)
