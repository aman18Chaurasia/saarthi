"""Mock TTS provider for testing when ElevenLabs quota is exhausted.

Returns silent PCM audio with realistic chunk timing to simulate streaming TTS.
Phase 1 verification only — not for production use.
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from .base import BaseTTSProvider


class MockTTSProvider(BaseTTSProvider):
    """Mock TTS that returns silent audio with simulated streaming latency."""

    def __init__(self, first_byte_delay_ms: float = 60, chunk_size: int = 4096) -> None:
        self._first_byte_delay = first_byte_delay_ms / 1000
        self._chunk_size = chunk_size

    async def synthesize(self, text: str) -> bytes:
        """Return silent audio for entire text."""
        # ~150 chars = 3s of audio at 16kHz mono PCM16
        duration_s = len(text) * 0.02
        num_samples = int(16000 * duration_s)
        return b"\x00\x00" * num_samples  # silent PCM int16

    async def stream(
        self,
        text: str,
        voice_id: str | None = None,
        model: str = "mock",
        timeout_s: float = 3.0,
        max_retries: int = 2,
    ) -> AsyncIterator[bytes]:
        """Yield silent audio chunks with realistic timing."""
        # Simulate first-byte latency
        await asyncio.sleep(self._first_byte_delay)

        # Calculate total duration (~150 chars/s speech rate)
        duration_s = max(0.5, len(text) * 0.02)
        num_samples = int(16000 * duration_s)
        total_bytes = num_samples * 2  # int16 = 2 bytes/sample

        # Yield in chunks
        offset = 0
        while offset < total_bytes:
            chunk_bytes = min(self._chunk_size, total_bytes - offset)
            yield b"\x00\x00" * (chunk_bytes // 2)
            offset += chunk_bytes
            await asyncio.sleep(0.01)  # Simulate network streaming
