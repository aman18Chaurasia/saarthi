"""Custom Presidio recognizers for Indian BFSI PII.

Aadhaar  — 12-digit number with Verhoeff check digit, first digit 2-9.
PAN      — 10-char alphanumeric: AAAAA0000A (5 upper letters, 4 digits, 1 upper letter).
Card     — 13–19 digit number that passes the Luhn check.
PhoneIN  — 10-digit Indian mobile starting with 6-9, optionally prefixed +91/0.
"""
from __future__ import annotations

import re

from presidio_analyzer import EntityRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts

# ── Verhoeff tables (same as fixtures/fake_identifiers.py) ────────────────────

_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]


def _verhoeff_valid(number: str) -> bool:
    """Return True iff the digit string passes the Verhoeff check."""
    if not number.isdigit():
        return False
    c = 0
    for i, ch in enumerate(reversed(number)):
        c = _D[c][_P[i % 8][int(ch)]]
    return c == 0


def _luhn_valid(number: str) -> bool:
    """Return True iff the digit string passes the Luhn check."""
    if not number.isdigit():
        return False
    total = 0
    for i, ch in enumerate(reversed(number)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


# ── Aadhaar recognizer ────────────────────────────────────────────────────────

# Matches 12-digit numbers whose first digit is 2-9, optionally space/hyphen
# separated as 4-4-4 (common print format).  Negative lookbehind/ahead prevent
# matching 12-digit substrings inside longer numbers.
_AADHAAR_RE = re.compile(
    r"(?<!\d)"
    r"([2-9]\d{3}[\s\-]?\d{4}[\s\-]?\d{4})"
    r"(?!\d)"
)


class AadhaarRecognizer(EntityRecognizer):
    """Recognises 12-digit Verhoeff-valid Aadhaar numbers."""

    ENTITIES = ["AADHAAR_NUMBER"]

    def __init__(self) -> None:
        super().__init__(
            supported_entities=self.ENTITIES,
            name="AadhaarRecognizer",
            supported_language="en",
        )

    def load(self) -> None:  # required by base class
        pass

    def analyze(
        self, text: str, entities: list[str], nlp_artifacts: NlpArtifacts | None = None
    ) -> list[RecognizerResult]:
        results: list[RecognizerResult] = []
        for m in _AADHAAR_RE.finditer(text):
            digits = re.sub(r"[\s\-]", "", m.group(1))
            if len(digits) == 12 and _verhoeff_valid(digits):
                results.append(
                    RecognizerResult(
                        entity_type="AADHAAR_NUMBER",
                        start=m.start(),
                        end=m.end(),
                        score=0.95,
                    )
                )
        return results


# ── PAN recognizer ────────────────────────────────────────────────────────────

# Strict format: 5 uppercase letters, 4 digits, 1 uppercase letter.
# Negative lookahead/behind prevent partial matches.
_PAN_RE = re.compile(r"(?<![A-Z0-9])([A-Z]{5}[0-9]{4}[A-Z])(?![A-Z0-9])")


class PANRecognizer(EntityRecognizer):
    """Recognises Indian Permanent Account Numbers (PAN)."""

    ENTITIES = ["IN_PAN"]

    def __init__(self) -> None:
        super().__init__(
            supported_entities=self.ENTITIES,
            name="PANRecognizer",
            supported_language="en",
        )

    def load(self) -> None:
        pass

    def analyze(
        self, text: str, entities: list[str], nlp_artifacts: NlpArtifacts | None = None
    ) -> list[RecognizerResult]:
        return [
            RecognizerResult(
                entity_type="IN_PAN",
                start=m.start(),
                end=m.end(),
                score=0.9,
            )
            for m in _PAN_RE.finditer(text)
        ]


# ── Luhn card recognizer ──────────────────────────────────────────────────────

# 13–19 consecutive digits that pass Luhn.  Spaces/hyphens every 4 digits
# allowed (common card print format).
_CARD_RE = re.compile(
    r"(?<!\d)"
    r"(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{1,7})"
    r"(?!\d)"
)


class LuhnCardRecognizer(EntityRecognizer):
    """Recognises Luhn-valid payment card numbers (13–19 digits)."""

    ENTITIES = ["CREDIT_CARD"]

    def __init__(self) -> None:
        super().__init__(
            supported_entities=self.ENTITIES,
            name="LuhnCardRecognizer",
            supported_language="en",
        )

    def load(self) -> None:
        pass

    def analyze(
        self, text: str, entities: list[str], nlp_artifacts: NlpArtifacts | None = None
    ) -> list[RecognizerResult]:
        results: list[RecognizerResult] = []
        for m in _CARD_RE.finditer(text):
            digits = re.sub(r"[\s\-]", "", m.group(1))
            if 13 <= len(digits) <= 19 and _luhn_valid(digits):
                results.append(
                    RecognizerResult(
                        entity_type="CREDIT_CARD",
                        start=m.start(),
                        end=m.end(),
                        score=0.9,
                    )
                )
        return results


# ── Indian phone recognizer ───────────────────────────────────────────────────

# Matches 10-digit numbers starting with 6-9, with optional +91 / 0 prefix.
_PHONE_IN_RE = re.compile(
    r"(?<!\d)"
    r"(?:\+91[\s\-]?|0)?([6-9]\d{9})"
    r"(?!\d)"
)


class PhoneINRecognizer(EntityRecognizer):
    """Recognises Indian mobile numbers (10 digits, starting 6-9)."""

    ENTITIES = ["IN_PHONE"]

    def __init__(self) -> None:
        super().__init__(
            supported_entities=self.ENTITIES,
            name="PhoneINRecognizer",
            supported_language="en",
        )

    def load(self) -> None:
        pass

    def analyze(
        self, text: str, entities: list[str], nlp_artifacts: NlpArtifacts | None = None
    ) -> list[RecognizerResult]:
        return [
            RecognizerResult(
                entity_type="IN_PHONE",
                start=m.start(0),
                end=m.end(0),
                score=0.85,
            )
            for m in _PHONE_IN_RE.finditer(text)
        ]
