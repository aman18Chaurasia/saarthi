"""ASR frame processor: buffers speech audio and calls Groq Whisper.

On UserStartedSpeakingFrame: begins accumulating AudioRawFrame bytes.
On UserStoppedSpeakingFrame: flushes the buffer to the transcribe_fn, emits
  TranscriptionFrame + LatencyFrame.

transcribe_fn is injectable so tests can mock it without touching httpx.
"""
from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from pipecat.frames.frames import (
    AudioRawFrame,
    Frame,
    TranscriptionFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from frames import LatencyFrame


class ASRProcessor(FrameProcessor):
    """Buffer speech audio then transcribe on end-of-speech.

    Args:
        transcribe_fn: ``async (pcm_bytes: bytes) -> str``; called with the
                       raw 16-bit 16 kHz PCM of the entire utterance.
                       In production this wraps Groq Whisper; in tests it is mocked.
        user_id:       Forwarded into TranscriptionFrame (caller supplies call_id).
    """

    def __init__(
        self,
        transcribe_fn: Callable[[bytes], Awaitable[str]],
        user_id: str = "user",
    ) -> None:
        super().__init__()
        self._transcribe_fn = transcribe_fn
        self._user_id = user_id
        self._collecting = False
        self._audio_buf: bytearray = bytearray()

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)

        if isinstance(frame, UserStartedSpeakingFrame):
            self._collecting = True
            self._audio_buf.clear()
            await self.push_frame(frame, direction)

        elif isinstance(frame, AudioRawFrame) and self._collecting:
            self._audio_buf.extend(frame.audio)
            await self.push_frame(frame, direction)

        elif isinstance(frame, UserStoppedSpeakingFrame):
            self._collecting = False
            await self.push_frame(frame, direction)

            if self._audio_buf:
                pcm = bytes(self._audio_buf)
                self._audio_buf.clear()

                t0 = time.perf_counter_ns()
                text = await self._transcribe_fn(pcm)
                asr_ms = (time.perf_counter_ns() - t0) / 1_000_000

                if text:
                    await self.push_frame(
                        TranscriptionFrame(
                            text=text,
                            user_id=self._user_id,
                            timestamp=str(int(t0 // 1_000_000)),
                            finalized=True,
                        ),
                        direction,
                    )
                await self.push_frame(
                    LatencyFrame(hop="asr", duration_ms=asr_ms),
                    direction,
                )

        else:
            await self.push_frame(frame, direction)
