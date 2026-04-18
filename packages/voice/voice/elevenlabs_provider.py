"""ElevenLabs TTS provider — buffered synthesize() and streaming stream().

stream() uses httpx directly (not the ElevenLabs SDK) so that:
  • pytest-httpx can intercept every request in tests.
  • The retry loop, Retry-After handling, and first-byte timeout are explicit.
  • The XTTS fallback can swap behind the same BaseTTSProvider interface.
"""
from __future__ import annotations

import asyncio
import os
import time
from collections.abc import AsyncIterator

import httpx
from elevenlabs.client import AsyncElevenLabs

from .base import BaseTTSProvider
from .errors import TTSAPIError, TTSStreamError, TTSTimeoutError

_ELEVENLABS_BASE_URL = "https://api.elevenlabs.io"
_DEFAULT_MODEL = "eleven_turbo_v2_5"
_DEFAULT_OUTPUT_FORMAT = "pcm_16000"
_BACKOFF_S = 0.150


def _parse_retry_after(headers: httpx.Headers) -> float:
    try:
        return float(headers.get("retry-after", ""))
    except (ValueError, TypeError):
        return _BACKOFF_S


class ElevenLabsProvider(BaseTTSProvider):
    """TTS provider backed by the ElevenLabs API.

    synthesize() — non-streaming; returns all audio bytes at once (legacy).
    stream()     — async generator; yields PCM int16 chunks as they arrive.
    """

    def __init__(self) -> None:
        self._api_key: str = os.environ["ELEVENLABS_API_KEY"]
        self._voice_id: str = os.environ.get("ELEVENLABS_VOICE_ID", "Rachel")
        # SDK client kept for synthesize() backward compatibility
        self._sdk_client = AsyncElevenLabs(api_key=self._api_key)
        # Populated by stream() when the first audio chunk arrives
        self.last_first_byte_ms: float | None = None

    # ── Legacy non-streaming method (BaseTTSProvider contract) ───────────────

    async def synthesize(self, text: str) -> bytes:
        audio_iter = await self._sdk_client.generate(
            text=text,
            voice=self._voice_id,
            model="eleven_turbo_v2",
        )
        chunks: list[bytes] = []
        async for chunk in audio_iter:
            chunks.append(chunk)
        return b"".join(chunks)

    # ── Streaming method (ADR 0002 §1, §7.3) ─────────────────────────────────

    async def stream(
        self,
        text: str,
        voice_id: str | None = None,
        model: str = _DEFAULT_MODEL,
        timeout_s: float = 3.0,
        max_retries: int = 2,
    ) -> AsyncIterator[bytes]:
        """Stream PCM int16 audio from ElevenLabs.

        Yields bytes chunks as they arrive from the API.  The first-byte latency
        is recorded in ``self.last_first_byte_ms`` after each successful stream.

        Retry policy (ADR 0002 §7.3):
          • httpx timeout / first-byte timeout → retry up to max_retries.
          • HTTP 5xx                           → retry.
          • HTTP 429                           → sleep Retry-After, retry.
          • HTTP 4xx (≠ 429)                  → raise TTSAPIError immediately.
          • Mid-stream connection drop         → raise TTSStreamError (no retry).
          • Retries exhausted                  → raise TTSTimeoutError or TTSAPIError.
        """
        effective_voice = voice_id or self._voice_id
        last_exc: Exception | None = None
        prev_was_429 = False

        for attempt in range(max_retries + 1):
            if attempt > 0 and not prev_was_429:
                await asyncio.sleep(_BACKOFF_S)
            prev_was_429 = False

            try:
                req_start = time.perf_counter()
                first_byte = True

                async for chunk in self._stream_once(text, effective_voice, model, timeout_s):
                    if first_byte:
                        self.last_first_byte_ms = (time.perf_counter() - req_start) * 1000
                        first_byte = False
                    yield chunk

                return  # Successful completion

            except TTSStreamError:
                raise  # Mid-stream: never retry
            except (httpx.TimeoutException, asyncio.TimeoutError) as exc:
                last_exc = exc
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status == 429:
                    await asyncio.sleep(_parse_retry_after(exc.response.headers))
                    prev_was_429 = True
                    last_exc = exc
                elif 400 <= status < 500:
                    # exc.response.text is unreadable inside client.stream() context
                    raise TTSAPIError(
                        f"ElevenLabs API error {status}",
                        status_code=status,
                    ) from exc
                else:
                    last_exc = exc

        # All retries exhausted
        if isinstance(last_exc, (httpx.TimeoutException, asyncio.TimeoutError)):
            raise TTSTimeoutError(
                f"ElevenLabs first-byte timeout after {max_retries + 1} attempt(s)"
            ) from last_exc
        raise TTSAPIError(
            f"ElevenLabs failed after {max_retries + 1} attempt(s): {last_exc}",
            status_code=getattr(getattr(last_exc, "response", None), "status_code", None),
        ) from last_exc

    # ── Internal HTTP helper ──────────────────────────────────────────────────

    async def _stream_once(
        self,
        text: str,
        voice_id: str,
        model: str,
        timeout_s: float,
    ) -> AsyncIterator[bytes]:
        """Single streaming attempt — used by stream() retry loop.

        Raises httpx.TimeoutException / HTTPStatusError before any yield (retry-safe).
        Raises TTSStreamError if the connection drops after the first chunk.
        """
        url = f"{_ELEVENLABS_BASE_URL}/v1/text-to-speech/{voice_id}/stream"
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_s)  # applies to connect, read, write, pool
        ) as client:
            async with client.stream(
                "POST",
                url,
                headers={
                    "xi-api-key": self._api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "model_id": model,
                    "output_format": _DEFAULT_OUTPUT_FORMAT,
                },
            ) as response:
                response.raise_for_status()
                first_byte_received = False
                try:
                    async for chunk in response.aiter_bytes(chunk_size=4096):
                        if chunk:
                            first_byte_received = True
                            yield chunk
                except Exception as exc:
                    if first_byte_received:
                        raise TTSStreamError(
                            f"Mid-stream connection failure: {exc}"
                        ) from exc
                    raise  # Pre-first-byte failure → let retry loop handle it
