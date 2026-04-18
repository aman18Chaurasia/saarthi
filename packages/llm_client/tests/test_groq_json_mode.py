"""Tests for GroqProvider.json_mode() — all HTTP intercepted via pytest-httpx.

10 required tests (a–j) + 1 optional integration smoke test.
No real network calls in the required suite; the integration test is skipped
unless GROQ_API_KEY is present in the environment.
"""
from __future__ import annotations

import asyncio
import json
import os
from unittest.mock import AsyncMock, call

import httpx
import pytest

from llm_client.errors import LLMAPIError, LLMParseError, LLMTimeoutError
from llm_client.groq_provider import GroqProvider
from llm_client.schema import StructuredAgentResponse

# ── Shared helpers ────────────────────────────────────────────────────────────

_MESSAGES = [{"role": "user", "content": "test message"}]


def _groq_body(content: str) -> dict:
    """Minimal Groq-shaped response body with the given content string."""
    return {
        "id": "test-id",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
    }


def _valid_content() -> str:
    return json.dumps(
        {
            "classified_intent": "affirm",
            "slots_extracted": {"name_confirmed": True},
            "agent_turn_text": "Hello, how can I help?",
        }
    )


@pytest.fixture
def provider(monkeypatch: pytest.MonkeyPatch) -> GroqProvider:
    monkeypatch.setenv("GROQ_API_KEY", "test-key-not-real")
    monkeypatch.setenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    return GroqProvider()


# ── Test a: Happy path ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_a_happy_path_parses_structured_response(
    provider: GroqProvider, httpx_mock: object
) -> None:
    httpx_mock.add_response(json=_groq_body(_valid_content()))  # type: ignore[attr-defined]

    result = await provider.json_mode(_MESSAGES, StructuredAgentResponse)

    assert isinstance(result, StructuredAgentResponse)
    assert result.classified_intent == "affirm"
    assert result.slots_extracted == {"name_confirmed": True}
    assert result.agent_turn_text == "Hello, how can I help?"


# ── Test b: Malformed JSON → LLMParseError (no retry) ───────────────────────

@pytest.mark.asyncio
async def test_b_malformed_json_raises_parse_error_without_retry(
    provider: GroqProvider, httpx_mock: object
) -> None:
    httpx_mock.add_response(json=_groq_body("not {{ valid json at all"))  # type: ignore[attr-defined]

    with pytest.raises(LLMParseError):
        await provider.json_mode(_MESSAGES, StructuredAgentResponse)

    # Only one request must have been made — parse errors are not retried
    assert len(httpx_mock.get_requests()) == 1  # type: ignore[attr-defined]


# ── Test c: Missing required field → LLMParseError ───────────────────────────

@pytest.mark.asyncio
async def test_c_missing_required_field_raises_parse_error(
    provider: GroqProvider, httpx_mock: object
) -> None:
    # agent_turn_text is required; omitting it must trigger ValidationError
    partial = json.dumps({"classified_intent": "affirm", "slots_extracted": {}})
    httpx_mock.add_response(json=_groq_body(partial))  # type: ignore[attr-defined]

    with pytest.raises(LLMParseError):
        await provider.json_mode(_MESSAGES, StructuredAgentResponse)

    assert len(httpx_mock.get_requests()) == 1  # type: ignore[attr-defined]


# ── Test d: HTTP 500 × 2 then success on 3rd attempt ────────────────────────

@pytest.mark.asyncio
async def test_d_500_retries_twice_then_succeeds(
    provider: GroqProvider, httpx_mock: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    httpx_mock.add_response(status_code=500, text="Internal Server Error")  # type: ignore[attr-defined]
    httpx_mock.add_response(status_code=500, text="Internal Server Error")  # type: ignore[attr-defined]
    httpx_mock.add_response(json=_groq_body(_valid_content()))  # type: ignore[attr-defined]

    result = await provider.json_mode(_MESSAGES, StructuredAgentResponse, max_retries=2)

    assert result.classified_intent == "affirm"
    assert len(httpx_mock.get_requests()) == 3  # type: ignore[attr-defined]


# ── Test e: HTTP 500 all retries exhausted → LLMAPIError ────────────────────

@pytest.mark.asyncio
async def test_e_500_all_retries_exhausted_raises_api_error(
    provider: GroqProvider, httpx_mock: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    for _ in range(3):
        httpx_mock.add_response(status_code=500, text="Internal Server Error")  # type: ignore[attr-defined]

    with pytest.raises(LLMAPIError):
        await provider.json_mode(_MESSAGES, StructuredAgentResponse, max_retries=2)

    assert len(httpx_mock.get_requests()) == 3  # type: ignore[attr-defined]


# ── Test f: HTTP 429 with Retry-After → waits, retries, succeeds ────────────

@pytest.mark.asyncio
async def test_f_429_respects_retry_after_header_and_succeeds(
    provider: GroqProvider, httpx_mock: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    sleep_mock = AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", sleep_mock)
    httpx_mock.add_response(  # type: ignore[attr-defined]
        status_code=429,
        headers={"Retry-After": "0"},
        text="Too Many Requests",
    )
    httpx_mock.add_response(json=_groq_body(_valid_content()))  # type: ignore[attr-defined]

    result = await provider.json_mode(_MESSAGES, StructuredAgentResponse, max_retries=2)

    assert result.classified_intent == "affirm"
    # asyncio.sleep must have been called with Retry-After value (0.0 seconds)
    sleep_mock.assert_any_call(0.0)


# ── Test g: HTTP 400 → LLMAPIError immediately, no retry ────────────────────

@pytest.mark.asyncio
async def test_g_400_raises_api_error_immediately_without_retry(
    provider: GroqProvider, httpx_mock: object
) -> None:
    httpx_mock.add_response(status_code=400, text="Bad Request")  # type: ignore[attr-defined]

    with pytest.raises(LLMAPIError) as exc_info:
        await provider.json_mode(_MESSAGES, StructuredAgentResponse)

    assert exc_info.value.status_code == 400
    # Must not have retried — exactly one request made
    assert len(httpx_mock.get_requests()) == 1  # type: ignore[attr-defined]


# ── Test h: Timeout retries then raises LLMTimeoutError ──────────────────────

@pytest.mark.asyncio
async def test_h_timeout_retries_then_raises_timeout_error(
    provider: GroqProvider, httpx_mock: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    for _ in range(3):
        httpx_mock.add_exception(httpx.TimeoutException("Request timed out"))  # type: ignore[attr-defined]

    with pytest.raises(LLMTimeoutError):
        await provider.json_mode(_MESSAGES, StructuredAgentResponse, max_retries=2)

    assert len(httpx_mock.get_requests()) == 3  # type: ignore[attr-defined]


# ── Test i: Backoff delay is 150 ms between attempts ────────────────────────

@pytest.mark.asyncio
async def test_i_backoff_timing_150ms_between_attempts(
    provider: GroqProvider, httpx_mock: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    sleep_calls: list[float] = []

    async def capture_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    monkeypatch.setattr(asyncio, "sleep", capture_sleep)
    httpx_mock.add_response(status_code=500, text="Error")  # type: ignore[attr-defined]
    httpx_mock.add_response(status_code=500, text="Error")  # type: ignore[attr-defined]
    httpx_mock.add_response(json=_groq_body(_valid_content()))  # type: ignore[attr-defined]

    await provider.json_mode(_MESSAGES, StructuredAgentResponse, max_retries=2, backoff_ms=150)

    # Two sleeps: before attempt 1 and before attempt 2
    assert len(sleep_calls) == 2
    assert sleep_calls[0] == pytest.approx(0.150)
    assert sleep_calls[1] == pytest.approx(0.150)


# ── Test j: Default model resolved from GROQ_MODEL env var ──────────────────

@pytest.mark.asyncio
async def test_j_default_model_resolved_from_env(
    httpx_mock: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key-not-real")
    monkeypatch.setenv("GROQ_MODEL", "custom-env-model-name")
    # Create provider inside test so env var is read fresh
    local_provider = GroqProvider()

    httpx_mock.add_response(json=_groq_body(_valid_content()))  # type: ignore[attr-defined]

    await local_provider.json_mode(_MESSAGES, StructuredAgentResponse, model=None)

    requests = httpx_mock.get_requests()  # type: ignore[attr-defined]
    assert len(requests) == 1
    body = json.loads(requests[0].content)
    assert body["model"] == "custom-env-model-name"


# ── Bonus: Integration smoke test (skipped unless GROQ_API_KEY present) ──────

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.environ.get("GROQ_API_KEY"),
    reason="GROQ_API_KEY not set — skipped in default CI",
)
async def test_bonus_integration_real_groq_call() -> None:
    live_provider = GroqProvider()
    messages: list = [
        {
            "role": "system",
            "content": (
                'You must respond only with valid JSON: '
                '{"classified_intent":"affirm","slots_extracted":{},"agent_turn_text":"Hello!"}'
            ),
        },
        {"role": "user", "content": "Yes, I agree."},
    ]
    result = await live_provider.json_mode(messages, StructuredAgentResponse)
    assert isinstance(result, StructuredAgentResponse)
    assert result.classified_intent in {"affirm", "deny", "provide_value", "unclear"}
    assert result.agent_turn_text
