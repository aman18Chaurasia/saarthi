"""Presidio redaction tests — all cases from ADR 0002 §11.1.

Valid PII must be redacted; structurally invalid values must NOT be redacted.
Synthetic test data comes exclusively from fixtures/fake_identifiers.py.
"""
from __future__ import annotations

import logging
import random
import sys
from pathlib import Path

import pytest

# Make fixtures/ importable without installing it as a package.
sys.path.insert(0, str(Path(__file__).parents[3] / "fixtures"))
from fake_identifiers import fake_aadhaar, fake_card, fake_pan  # noqa: E402

from guardrail.redact import redact_str
from guardrail.formatter import RedactingFormatter

_RNG = random.Random(42)


# ── helpers ───────────────────────────────────────────────────────────────────

def _flip_last_digit(s: str) -> str:
    """Return s with its last character replaced by a different digit."""
    last = int(s[-1])
    replacement = (last + 1) % 10
    return s[:-1] + str(replacement)


# ── Aadhaar ───────────────────────────────────────────────────────────────────

def test_valid_aadhaar_is_redacted() -> None:
    aadhaar = fake_aadhaar(_RNG)
    result = redact_str(f"My Aadhaar is {aadhaar}.")
    assert "<AADHAAR_REDACTED>" in result
    assert aadhaar not in result


def test_invalid_checksum_aadhaar_not_redacted() -> None:
    """Flip the check digit so Verhoeff validation fails."""
    valid = fake_aadhaar(_RNG)
    invalid = _flip_last_digit(valid)
    # Ensure we actually broke the checksum (extremely unlikely to still be valid)
    assert invalid != valid
    result = redact_str(f"My Aadhaar is {invalid}.")
    assert "<AADHAAR_REDACTED>" not in result
    assert invalid in result


def test_random_12_digit_not_redacted() -> None:
    """A random 12-digit number starting with 2-9 that isn't Verhoeff-valid."""
    # Use a known non-Verhoeff number: all zeros except first digit
    non_aadhaar = "200000000000"
    result = redact_str(f"Number: {non_aadhaar}")
    assert "<AADHAAR_REDACTED>" not in result
    assert non_aadhaar in result


# ── PAN ───────────────────────────────────────────────────────────────────────

def test_valid_pan_is_redacted() -> None:
    pan = fake_pan(_RNG)
    result = redact_str(f"PAN card: {pan}")
    assert "<PAN_REDACTED>" in result
    assert pan not in result


def test_invalid_pan_pattern_not_redacted() -> None:
    """Lowercase PAN should not match — recogniser requires uppercase."""
    pan = fake_pan(_RNG).lower()
    result = redact_str(f"pan: {pan}")
    assert "<PAN_REDACTED>" not in result


# ── Luhn card ─────────────────────────────────────────────────────────────────

def test_luhn_valid_card_is_redacted() -> None:
    card = fake_card(rng=_RNG)
    result = redact_str(f"Card number: {card}")
    assert "<CARD_REDACTED>" in result
    assert card not in result


def test_luhn_invalid_card_not_redacted() -> None:
    """Flip the last digit so the Luhn check fails."""
    valid = fake_card(rng=_RNG)
    invalid = _flip_last_digit(valid)
    result = redact_str(f"Card: {invalid}")
    assert "<CARD_REDACTED>" not in result
    assert invalid in result


# ── Indian phone ──────────────────────────────────────────────────────────────

def test_indian_phone_is_redacted() -> None:
    phone = "9876543210"
    result = redact_str(f"Call me at {phone}.")
    assert "<PHONE_REDACTED>" in result
    assert phone not in result


def test_indian_phone_with_country_code_is_redacted() -> None:
    result = redact_str("Reach me at +91 9876543210 please.")
    assert "<PHONE_REDACTED>" in result


# ── Built-in recogniser sanity check ─────────────────────────────────────────

def test_email_address_is_redacted() -> None:
    result = redact_str("Send details to customer@example.com please.")
    assert "<EMAIL_REDACTED>" in result
    assert "customer@example.com" not in result


# ── RedactingFormatter ────────────────────────────────────────────────────────

def test_redacting_formatter_masks_aadhaar_in_log() -> None:
    aadhaar = fake_aadhaar(_RNG)
    logger = logging.getLogger("test.redacting_formatter")
    logger.setLevel(logging.DEBUG)

    handler = logging.handlers_store = logging.StreamHandler()
    formatter = RedactingFormatter("%(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    records: list[str] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(self.format(record))

    capture = _Capture()
    capture.setFormatter(formatter)
    logger.addHandler(capture)

    logger.warning("Customer aadhaar: %s", aadhaar)

    logger.removeHandler(handler)
    logger.removeHandler(capture)

    assert records, "No log records captured"
    assert "<AADHAAR_REDACTED>" in records[-1]
    assert aadhaar not in records[-1]


def test_redacting_formatter_passes_non_pii_unchanged() -> None:
    logger = logging.getLogger("test.formatter_passthrough")
    logger.setLevel(logging.DEBUG)
    records: list[str] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(self.format(record))

    capture = _Capture()
    capture.setFormatter(RedactingFormatter("%(message)s"))
    logger.addHandler(capture)
    logger.info("Pipeline started for product personal_loan")
    logger.removeHandler(capture)

    assert "Pipeline started for product personal_loan" in records[-1]
