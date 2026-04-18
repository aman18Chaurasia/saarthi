"""Custom exceptions for the LLM client layer.

These are raised by json_mode() so callers (dialog nodes) can decide
how to handle each failure mode without importing groq or httpx directly.
"""
from __future__ import annotations


class LLMTimeoutError(Exception):
    """Raised when the LLM API times out after all retry attempts are exhausted."""


class LLMParseError(Exception):
    """Raised when the LLM response cannot be parsed as valid JSON or fails
    Pydantic validation against the requested response_model.

    Not retried — the server produced a response; repeating the same request
    will likely produce the same junk. The dialog node should treat this as
    classified_intent='unclear' and increment retry_count.
    """


class LLMAPIError(Exception):
    """Raised when the LLM API returns an unrecoverable error (4xx other than 429,
    or 5xx after retries exhausted).
    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
