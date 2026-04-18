"""Groq LLM provider — streaming chat and JSON-mode structured output.

chat()       — thin wrapper around the Groq SDK; used by legacy callers.
json_mode()  — direct httpx call with structured retry/error handling;
               used by the dialog pipeline (commit 7+) for every agent turn.

json_mode() uses httpx directly (not the Groq SDK) so that:
  • pytest-httpx can intercept every request in tests.
  • The retry loop, Retry-After handling, and timeout logic are explicit.
"""
from __future__ import annotations

import asyncio
import json
import os

import httpx
from groq import AsyncGroq
from pydantic import BaseModel, ValidationError

from .base import BaseChatProvider
from .errors import LLMAPIError, LLMParseError, LLMTimeoutError
from .schema import ChatMessage, StructuredAgentResponse  # noqa: F401  (re-exported)

_GROQ_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"


def _parse_retry_after(headers: httpx.Headers) -> float:
    """Return the Retry-After delay in seconds (float).
    Defaults to 1.0 s when the header is absent or unparseable.
    """
    value = headers.get("retry-after", "")
    try:
        return float(value)
    except (ValueError, TypeError):
        return 1.0


class GroqProvider(BaseChatProvider):
    def __init__(self) -> None:
        self._api_key: str = os.environ["GROQ_API_KEY"]
        self._client = AsyncGroq(api_key=self._api_key)
        self._model: str = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    # ── Existing chat() method (unchanged) ────────────────────────────────────

    async def chat(self, messages: list[dict[str, str]]) -> str:
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
        )
        content = resp.choices[0].message.content
        return content or ""

    # ── JSON-mode structured call ──────────────────────────────────────────────

    async def json_mode(
        self,
        messages: list[ChatMessage],
        response_model: type[BaseModel],
        model: str | None = None,
        timeout_s: float = 5.0,
        max_retries: int = 2,
        backoff_ms: int = 150,
    ) -> BaseModel:
        """Call Groq in JSON mode, parse the response into *response_model*.

        Retry policy (ADR 0002 §7.2):
          • httpx timeout / asyncio.TimeoutError → retry with backoff, up to max_retries.
          • HTTP 5xx                              → retry with backoff.
          • HTTP 429 with Retry-After header      → wait Retry-After seconds, then retry.
          • HTTP 4xx (≠ 429)                      → raise LLMAPIError immediately.
          • JSON parse / Pydantic validation fail → raise LLMParseError (no retry;
            the dialog node treats this as classified_intent='unclear').
          • Retries exhausted                     → raise LLMTimeoutError (timeout path)
                                                    or LLMAPIError (HTTP error path).

        Args:
            messages:       Chat messages in OpenAI format.
            response_model: Pydantic model class to validate the JSON response into.
            model:          Override GROQ_MODEL env var for this call.
            timeout_s:      Per-attempt HTTP timeout in seconds.
            max_retries:    Number of *extra* attempts after the first (0 = no retry).
            backoff_ms:     Sleep between retries in milliseconds.

        Returns:
            An instance of *response_model*.

        Raises:
            LLMParseError:   Server responded but JSON was invalid / schema mismatch.
            LLMTimeoutError: All attempts timed out.
            LLMAPIError:     4xx (non-429) immediately, or 5xx after retries exhausted.
        """
        effective_model = model or self._model
        last_exc: Exception | None = None
        # When the previous attempt got 429, we already slept for Retry-After;
        # skip the regular backoff at the top of the next iteration.
        prev_was_429: bool = False

        for attempt in range(max_retries + 1):
            if attempt > 0 and not prev_was_429:
                await asyncio.sleep(backoff_ms / 1000)
            prev_was_429 = False

            try:
                content = await self._post_once(messages, effective_model, timeout_s)
            except (httpx.TimeoutException, asyncio.TimeoutError) as exc:
                last_exc = exc
                continue
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status == 429:
                    await asyncio.sleep(_parse_retry_after(exc.response.headers))
                    prev_was_429 = True
                    last_exc = exc
                    continue
                if 400 <= status < 500:
                    raise LLMAPIError(
                        f"Groq API error {status}: {exc.response.text}",
                        status_code=status,
                    ) from exc
                # 5xx — retry
                last_exc = exc
                continue
            else:
                # Got a 2xx response — parse it now
                try:
                    return response_model.model_validate_json(content)
                except (json.JSONDecodeError, ValidationError) as exc:
                    raise LLMParseError(
                        f"Failed to parse Groq JSON response: {exc}"
                    ) from exc

        # All attempts exhausted
        if isinstance(last_exc, (httpx.TimeoutException, asyncio.TimeoutError)):
            raise LLMTimeoutError(
                f"Groq request timed out after {max_retries + 1} attempt(s)"
            ) from last_exc
        raise LLMAPIError(
            f"Groq API failed after {max_retries + 1} attempt(s): {last_exc}",
            status_code=getattr(getattr(last_exc, "response", None), "status_code", None),
        ) from last_exc

    # ── Internal HTTP helper ───────────────────────────────────────────────────

    async def _post_once(
        self,
        messages: list[ChatMessage],
        model: str,
        timeout_s: float,
    ) -> str:
        """Single POST to the Groq completions endpoint.

        Returns choices[0].message.content as a raw string.
        Raises httpx.HTTPStatusError on non-2xx.
        Raises httpx.TimeoutException on timeout.
        """
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            resp = await client.post(
                _GROQ_COMPLETIONS_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": list(messages),
                    "response_format": {"type": "json_object"},
                },
            )
            resp.raise_for_status()
            return str(resp.json()["choices"][0]["message"]["content"])
