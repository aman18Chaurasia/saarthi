"""Custom exceptions for the TTS voice layer (ADR 0002 §7.3).

Raised by ElevenLabsProvider.stream() so Pipecat frame processors and pipeline
code can handle each failure mode without importing httpx directly.
"""
from __future__ import annotations


class TTSTimeoutError(Exception):
    """First-byte timeout exceeded after all retry attempts are exhausted."""


class TTSAPIError(Exception):
    """HTTP error from the TTS API (4xx immediately, 5xx after retries exhausted)."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class TTSStreamError(Exception):
    """Connection dropped or read error after at least one audio chunk was received.

    Not retried — the caller (pipeline) must decide whether to continue without
    audio or surface the error to the dashboard. Phase 3 can add resume-with-seek.
    """
