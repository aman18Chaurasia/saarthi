"""TTS frame processor: streams ElevenLabs audio on TextFrame.

On TextFrame:
  1. Call ElevenLabsProvider.stream(text)
  2. Emit AudioRawFrame for each PCM chunk
  3. Emit LatencyFrame(hop="tts", duration_ms=first_byte_ms)
"""
from __future__ import annotations

import inspect
import logging
import time

from pipecat.frames.frames import ErrorFrame, Frame, TTSAudioRawFrame, TextFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from ..frames import LatencyFrame

_TTS_SAMPLE_RATE = 16000  # pcm_16000
_TTS_CHANNELS = 1
logger = logging.getLogger(__name__)


class TTSProcessor(FrameProcessor):
    """Streams TTS audio for each agent TextFrame.

    Args:
        tts_provider: ElevenLabsProvider instance (or any object with a
                      compatible ``stream(text) -> AsyncIterator[bytes]``).
        voice_id:     Optional voice override; defaults to ELEVENLABS_VOICE_ID.
    """

    def __init__(
        self,
        tts_provider: object,
        voice_id: str | None = None,
        language: str | None = None,
    ) -> None:
        super().__init__()
        self._provider = tts_provider
        self._voice_id = voice_id
        self._language = language

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)

        if type(frame) is not TextFrame:
            await self.push_frame(frame, direction)
            return

        t0 = time.perf_counter_ns()
        first_byte = True
        tts_first_byte_ms: float = 0.0

        kwargs: dict[str, object] = {}
        stream_fn = getattr(self._provider, "stream", None)
        stream_params = inspect.signature(stream_fn).parameters if stream_fn else {}
        if self._voice_id and "voice_id" in stream_params:
            kwargs["voice_id"] = self._voice_id
        if self._language and "language" in stream_params:
            kwargs["language"] = self._language

        await self.push_frame(frame, direction)

        try:
            async for chunk in self._provider.stream(frame.text, **kwargs):  # type: ignore[attr-defined]
                if first_byte:
                    tts_first_byte_ms = (time.perf_counter_ns() - t0) / 1_000_000
                    first_byte = False
                await self.push_frame(
                    TTSAudioRawFrame(
                        audio=chunk,
                        sample_rate=_TTS_SAMPLE_RATE,
                        num_channels=_TTS_CHANNELS,
                    ),
                    direction,
                )
        except Exception as exc:
            logger.exception("TTS synthesis failed")
            await self.push_frame(
                ErrorFrame(
                    error=f"TTS synthesis failed: {type(exc).__name__}: {exc}",
                    fatal=False,
                    processor=self,
                    exception=exc,
                ),
                direction,
            )
            return

        if not first_byte:  # at least one chunk was received
            await self.push_frame(
                LatencyFrame(hop="tts", duration_ms=tts_first_byte_ms),
                direction,
            )
