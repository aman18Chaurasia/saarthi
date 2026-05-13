"""ASR frame processor: buffers speech audio and calls Groq Whisper.

On UserStartedSpeakingFrame: begins accumulating AudioRawFrame bytes.
On UserStoppedSpeakingFrame: flushes the buffer to the transcribe_fn, emits
  TranscriptionFrame + LatencyFrame.

transcribe_fn is injectable so tests can mock it without touching httpx.
"""
from __future__ import annotations

import json
import os
import time
from collections.abc import Awaitable, Callable

import redis.asyncio as redis

from pipecat.frames.frames import (
    AudioRawFrame,
    Frame,
    TranscriptionFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from ..frames import LatencyFrame

# PII redaction
try:
    from guardrail.compliance import redact_pii
    REDACTION_AVAILABLE = True
except ImportError:
    REDACTION_AVAILABLE = False
    def redact_pii(text: str) -> str:
        return text

# Urdu→Hindi transliteration
# Note: indic-transliteration library doesn't support Urdu/Arabic script
# Urdu text will pass through as-is (Groq Whisper may handle it)
TRANSLITERATE_AVAILABLE = False  # Disabled - no library supports Urdu→Devanagari


def to_devanagari(text: str) -> str:
    """Convert Urdu/Arabic script to Devanagari (Hindi) if detected.

    Currently disabled - indic-transliteration doesn't support Urdu script.
    Urdu text passes through unchanged; Groq Whisper API may handle it.
    """
    # TODO: Find library that supports Urdu script transliteration
    # or rely on ASR model's native Urdu support
    return text


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

        # Redis for supervisor monitoring
        self._redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self._redis_client: redis.Redis | None = None

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

                # Skip transcription if audio too short (< 200ms = 6400 bytes at 16kHz mono)
                # Prevents hallucination from noise bursts
                MIN_AUDIO_BYTES = 6400
                if len(pcm) < MIN_AUDIO_BYTES:
                    return

                t0 = time.perf_counter_ns()
                text = await self._transcribe_fn(pcm)
                asr_ms = (time.perf_counter_ns() - t0) / 1_000_000

                # Convert Urdu→Hindi script if needed
                if text:
                    text = to_devanagari(text)

                # Redact PII before display/storage
                if text:
                    text_redacted = redact_pii(text)
                    # Publish redacted version to supervisor monitor
                    await self._publish_transcript(text_redacted, "customer")
                else:
                    text_redacted = text

                if text_redacted:
                    transcription = TranscriptionFrame(
                        text=text_redacted,
                        user_id=self._user_id,
                        timestamp=str(int(t0 // 1_000_000)),
                        finalized=True,
                    )
                    transcription.metadata["duration_ms"] = asr_ms
                    await self.push_frame(
                        transcription,
                        direction,
                    )
                await self.push_frame(
                    LatencyFrame(hop="asr", duration_ms=asr_ms),
                    direction,
                )

        else:
            await self.push_frame(frame, direction)

    async def _publish_transcript(self, text: str, speaker: str) -> None:
        """Publish transcript to Redis for supervisor monitoring."""
        try:
            if self._redis_client is None:
                self._redis_client = await redis.from_url(self._redis_url)

            message = json.dumps({
                "type": "transcript",
                "speaker": speaker,
                "text": text,
                "timestamp": time.time()
            })

            await self._redis_client.publish(
                f"supervisor:{self._user_id}:transcript",
                message
            )
        except Exception as e:
            # Don't fail the call if Redis publish fails
            print(f"[WARN] Failed to publish transcript: {e}")
