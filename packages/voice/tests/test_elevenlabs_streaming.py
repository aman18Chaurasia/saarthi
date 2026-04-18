"""Tests for ElevenLabsProvider.stream() — all HTTP intercepted via pytest-httpx.

8 required tests (a–h) + 1 optional integration smoke test.
No real network calls in the required suite.
"""
from __future__ import annotations

import asyncio
import os
from unittest.mock import AsyncMock

import httpx
import pytest
from pytest_httpx import IteratorStream

from voice.elevenlabs_provider import ElevenLabsProvider, _ELEVENLABS_BASE_URL
from voice.errors import TTSAPIError, TTSStreamError, TTSTimeoutError

# ── Helpers ───────────────────────────────────────────────────────────────────

_VOICE_ID = "test-voice-id"
_STREAM_URL = f"{_ELEVENLABS_BASE_URL}/v1/text-to-speech/{_VOICE_ID}/stream"

# Three discrete PCM chunks (4096 bytes each — matches chunk_size parameter)
_CHUNK_A = b"\x00\x01" * 2048   # 4096 bytes
_CHUNK_B = b"\x02\x03" * 2048   # 4096 bytes
_CHUNK_C = b"\x04\x05" * 2048   # 4096 bytes
_ALL_PCM = _CHUNK_A + _CHUNK_B + _CHUNK_C


@pytest.fixture
def provider(monkeypatch: pytest.MonkeyPatch) -> ElevenLabsProvider:
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key-not-real")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", _VOICE_ID)
    return ElevenLabsProvider()


async def _collect(provider: ElevenLabsProvider, text: str = "Hello.", **kwargs: object) -> bytes:
    """Drive provider.stream() to completion and return all bytes."""
    chunks: list[bytes] = []
    async for chunk in provider.stream(text, **kwargs):  # type: ignore[arg-type]
        chunks.append(chunk)
    return b"".join(chunks)


# ── Test a: Happy path — 3 chunks, total bytes match ─────────────────────────

@pytest.mark.asyncio
async def test_a_happy_path_yields_all_pcm_chunks(
    provider: ElevenLabsProvider, httpx_mock: object
) -> None:
    # IteratorStream delivers each list item as a separate chunk
    httpx_mock.add_response(  # type: ignore[attr-defined]
        stream=IteratorStream([_CHUNK_A, _CHUNK_B, _CHUNK_C]),
    )

    chunks: list[bytes] = []
    async for chunk in provider.stream("Hello!"):
        chunks.append(chunk)

    assert b"".join(chunks) == _ALL_PCM
    assert len(chunks) == 3


# ── Test b: First-byte timeout → retries → TTSTimeoutError ───────────────────

@pytest.mark.asyncio
async def test_b_first_byte_timeout_retries_then_raises(
    provider: ElevenLabsProvider, httpx_mock: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    for _ in range(3):
        httpx_mock.add_exception(httpx.TimeoutException("First byte timed out"))  # type: ignore[attr-defined]

    with pytest.raises(TTSTimeoutError):
        await _collect(provider)

    assert len(httpx_mock.get_requests()) == 3  # type: ignore[attr-defined]


# ── Test c: HTTP 500 retries 2×, succeeds on 3rd ─────────────────────────────

@pytest.mark.asyncio
async def test_c_500_retries_twice_then_succeeds(
    provider: ElevenLabsProvider, httpx_mock: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    httpx_mock.add_response(status_code=500, text="Internal Server Error")  # type: ignore[attr-defined]
    httpx_mock.add_response(status_code=500, text="Internal Server Error")  # type: ignore[attr-defined]
    httpx_mock.add_response(stream=IteratorStream([_CHUNK_A]))  # type: ignore[attr-defined]

    result = await _collect(provider)

    assert result == _CHUNK_A
    assert len(httpx_mock.get_requests()) == 3  # type: ignore[attr-defined]


# ── Test d: HTTP 429 with Retry-After → waits, retries, succeeds ─────────────

@pytest.mark.asyncio
async def test_d_429_respects_retry_after_and_succeeds(
    provider: ElevenLabsProvider, httpx_mock: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    sleep_mock = AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", sleep_mock)
    httpx_mock.add_response(  # type: ignore[attr-defined]
        status_code=429,
        headers={"Retry-After": "0"},
        text="Too Many Requests",
    )
    httpx_mock.add_response(stream=IteratorStream([_CHUNK_A]))  # type: ignore[attr-defined]

    result = await _collect(provider)

    assert result == _CHUNK_A
    # Retry-After sleep must have been called with 0.0 seconds
    sleep_mock.assert_any_call(0.0)


# ── Test e: HTTP 400 → TTSAPIError immediately, no retry ─────────────────────

@pytest.mark.asyncio
async def test_e_400_raises_api_error_immediately(
    provider: ElevenLabsProvider, httpx_mock: object
) -> None:
    httpx_mock.add_response(status_code=400, text="Bad Request")  # type: ignore[attr-defined]

    with pytest.raises(TTSAPIError) as exc_info:
        await _collect(provider)

    assert exc_info.value.status_code == 400
    assert len(httpx_mock.get_requests()) == 1  # type: ignore[attr-defined]


# ── Test f: Mid-stream connection drop → TTSStreamError ──────────────────────

@pytest.mark.asyncio
async def test_f_mid_stream_drop_raises_stream_error(
    provider: ElevenLabsProvider, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Simulate receiving 2 chunks then a connection drop."""

    async def _failing_stream_once(
        text: str, voice_id: str, model: str, timeout_s: float
    ) -> object:
        yield _CHUNK_A
        yield _CHUNK_B
        # _stream_once wraps transport errors as TTSStreamError after first byte;
        # raise it directly here to test stream()'s TTSStreamError handling.
        raise TTSStreamError("Mid-stream connection failure: Connection reset by peer")

    monkeypatch.setattr(provider, "_stream_once", _failing_stream_once)

    received: list[bytes] = []
    with pytest.raises(TTSStreamError):
        async for chunk in provider.stream("Hello!"):
            received.append(chunk)

    # The first two chunks were already received before the drop
    assert b"".join(received) == _CHUNK_A + _CHUNK_B


# ── Test g: Voice ID defaults to env var ──────────────────────────────────────

@pytest.mark.asyncio
async def test_g_voice_id_defaults_to_env_var(
    httpx_mock: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "env-voice-xyz")
    local_provider = ElevenLabsProvider()

    httpx_mock.add_response(stream=IteratorStream([_CHUNK_A]))  # type: ignore[attr-defined]
    await _collect(local_provider)

    requests = httpx_mock.get_requests()  # type: ignore[attr-defined]
    assert len(requests) == 1
    assert "env-voice-xyz" in str(requests[0].url)


# ── Test h: last_first_byte_ms populated after successful stream ──────────────

@pytest.mark.asyncio
async def test_h_last_first_byte_ms_populated_after_stream(
    provider: ElevenLabsProvider, httpx_mock: object
) -> None:
    assert provider.last_first_byte_ms is None  # Not set yet

    httpx_mock.add_response(stream=IteratorStream([_CHUNK_A, _CHUNK_B]))  # type: ignore[attr-defined]
    await _collect(provider)

    assert provider.last_first_byte_ms is not None
    assert provider.last_first_byte_ms >= 0.0  # Always non-negative


# ── Bonus: Integration smoke test (skipped unless ELEVENLABS_API_KEY present) ─

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.environ.get("ELEVENLABS_API_KEY"),
    reason="ELEVENLABS_API_KEY not set — skipped in default CI",
)
async def test_bonus_integration_real_elevenlabs_stream() -> None:
    live_provider = ElevenLabsProvider()
    chunks: list[bytes] = []
    async for chunk in live_provider.stream(
        "Testing. One, two, three.",
        model="eleven_turbo_v2_5",
    ):
        chunks.append(chunk)
        if len(b"".join(chunks)) > 8192:
            break  # Enough audio for a smoke test
    assert len(chunks) >= 1, "No audio chunks received from ElevenLabs"
    assert live_provider.last_first_byte_ms is not None
