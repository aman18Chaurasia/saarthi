"""Smart VAD with filler detection and interruption intent recognition.

Distinguishes between:
- Fillers ("um", "uh", "er") - ignore, let agent continue
- Real interruptions - stop agent immediately
- Backchannels ("haan", "okay") - acknowledge but continue
"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from pipecat.frames.frames import (
    AudioRawFrame,
    Frame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


class SmartVAD(FrameProcessor):
    """Smart Voice Activity Detection with intent recognition.

    Wraps standard VAD but adds intelligence to detect:
    - Fillers that should be ignored
    - Real interruptions that should stop agent
    - Backchannels that can be acknowledged without stopping
    """

    def __init__(
        self,
        transcribe_fn: Callable[[bytes], Awaitable[str]],
        base_vad: FrameProcessor,
    ):
        """Initialize smart VAD.

        Args:
            transcribe_fn: Quick transcription function for intent detection
            base_vad: Base VAD processor (e.g., WebRTCVAD)
        """
        super().__init__()
        self.transcribe_fn = transcribe_fn
        self.base_vad = base_vad
        self.audio_buffer: bytes = b""
        self.is_speaking = False

        # Filler words to ignore
        self.fillers = {
            "um", "uh", "er", "ah", "hmm", "mm", "eh",
            # Hindi fillers
            "हम्म", "अह", "एर"
        }

        # Backchannels - acknowledge but don't interrupt
        self.backchannels = {
            "haan", "हाँ", "okay", "ok", "ओके", "right", "yes",
            "theek", "ठीक", "achha", "अच्छा"
        }

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)

        # Pass through non-audio frames
        if not isinstance(frame, (AudioRawFrame, UserStartedSpeakingFrame, UserStoppedSpeakingFrame)):
            await self.push_frame(frame, direction)
            return

        # Handle speech start
        if isinstance(frame, UserStartedSpeakingFrame):
            self.is_speaking = True
            self.audio_buffer = b""
            # Don't push yet - wait to determine if it's real speech
            return

        # Accumulate audio during speech
        if isinstance(frame, AudioRawFrame) and self.is_speaking:
            self.audio_buffer += frame.audio
            await self.push_frame(frame, direction)
            return

        # Handle speech end - determine if it was real interruption
        if isinstance(frame, UserStoppedSpeakingFrame):
            self.is_speaking = False

            # Quick transcription to determine intent
            if self.audio_buffer:
                try:
                    text = await asyncio.wait_for(
                        self.transcribe_fn(self.audio_buffer),
                        timeout=0.5  # Quick, low-latency transcription
                    )
                    text_clean = text.strip().lower()

                    # Classify utterance
                    is_filler = text_clean in self.fillers
                    is_backchannel = text_clean in self.backchannels
                    is_real_speech = len(text_clean.split()) > 1 or (
                        not is_filler and not is_backchannel
                    )

                    if is_filler:
                        # Ignore fillers completely
                        return

                    if is_backchannel:
                        # Backchannel: push a different frame type for acknowledgment
                        # but don't interrupt agent's speech
                        backchannel_frame = UserStoppedSpeakingFrame()
                        backchannel_frame.metadata = {"type": "backchannel", "text": text}
                        await self.push_frame(backchannel_frame, direction)
                        return

                    if is_real_speech:
                        # Real interruption: push normal stopped speaking frame
                        await self.push_frame(frame, direction)
                        return

                except asyncio.TimeoutError:
                    # Transcription took too long, assume real speech
                    await self.push_frame(frame, direction)
                except Exception:
                    # Error in transcription, play it safe and assume real speech
                    await self.push_frame(frame, direction)
            else:
                # No audio captured, might be noise
                return

        # Default: pass through
        await self.push_frame(frame, direction)
