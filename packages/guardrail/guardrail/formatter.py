"""RedactingFormatter — a logging.Formatter that strips PII before emission.

Usage:
    import logging
    from guardrail.formatter import RedactingFormatter

    handler = logging.StreamHandler()
    handler.setFormatter(RedactingFormatter("%(levelname)s %(message)s"))
    logging.getLogger().addHandler(handler)

Any log message that reaches this formatter has its text run through
redact_str() before the final formatted string is returned.
"""
from __future__ import annotations

import logging

from .redact import redact_str


class RedactingFormatter(logging.Formatter):
    """Wraps a standard Formatter and redacts PII from every log record."""

    def format(self, record: logging.LogRecord) -> str:
        # Format normally first so % interpolation and exc_info are resolved.
        original = super().format(record)
        return redact_str(original)
