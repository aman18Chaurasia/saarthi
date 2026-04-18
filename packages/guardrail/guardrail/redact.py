"""Presidio-based PII redaction for SAARTHI.

Entry points:
    redact_str(text)          -> redacted string
    redact_dict(d)            -> shallow-copy dict with all string values redacted
    redact_transcript(turns)  -> list[dict] with 'text' fields redacted

Presidio runs after the call closes, before any DB write or log write.
It does NOT run before the LLM (LLM sees raw text for dialog coherence).
"""
from __future__ import annotations

from typing import Any

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from .recognizers import (
    AadhaarRecognizer,
    LuhnCardRecognizer,
    PANRecognizer,
    PhoneINRecognizer,
)

# ── Engine setup (module-level singletons; spaCy model loaded once) ───────────

def _build_analyzer() -> AnalyzerEngine:
    registry = RecognizerRegistry()
    registry.load_predefined_recognizers()  # EMAIL_ADDRESS, PERSON, PHONE_NUMBER, …

    for recognizer in (
        AadhaarRecognizer(),
        PANRecognizer(),
        LuhnCardRecognizer(),
        PhoneINRecognizer(),
    ):
        registry.add_recognizer(recognizer)

    return AnalyzerEngine(registry=registry)


_analyzer = _build_analyzer()
_anonymizer = AnonymizerEngine()

# Map entity type → placeholder label used in redacted output.
_OPERATORS: dict[str, OperatorConfig] = {
    "AADHAAR_NUMBER": OperatorConfig("replace", {"new_value": "<AADHAAR_REDACTED>"}),
    "IN_PAN":         OperatorConfig("replace", {"new_value": "<PAN_REDACTED>"}),
    "CREDIT_CARD":    OperatorConfig("replace", {"new_value": "<CARD_REDACTED>"}),
    "IN_PHONE":       OperatorConfig("replace", {"new_value": "<PHONE_REDACTED>"}),
    "EMAIL_ADDRESS":  OperatorConfig("replace", {"new_value": "<EMAIL_REDACTED>"}),
    "PERSON":         OperatorConfig("replace", {"new_value": "<PERSON_REDACTED>"}),
    "PHONE_NUMBER":   OperatorConfig("replace", {"new_value": "<PHONE_REDACTED>"}),
    "DEFAULT":        OperatorConfig("replace", {"new_value": "<REDACTED>"}),
}

_ENTITIES = list(_OPERATORS.keys())


def redact_str(text: str, language: str = "en") -> str:
    """Return *text* with all recognised PII replaced by placeholder tokens."""
    if not text:
        return text
    results = _analyzer.analyze(text=text, entities=_ENTITIES, language=language)
    if not results:
        return text
    anonymized = _anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators=_OPERATORS,
    )
    return anonymized.text


def redact_dict(data: dict[str, Any], language: str = "en") -> dict[str, Any]:
    """Shallow-copy *data* redacting every value that is a str."""
    return {
        k: (redact_str(v, language) if isinstance(v, str) else v)
        for k, v in data.items()
    }


def redact_transcript(
    turns: list[dict[str, Any]], language: str = "en"
) -> list[dict[str, Any]]:
    """Return a new list of turn dicts with the 'text' field of each redacted."""
    redacted = []
    for turn in turns:
        new_turn = dict(turn)
        if "text" in new_turn and isinstance(new_turn["text"], str):
            new_turn["text"] = redact_str(new_turn["text"], language)
        redacted.append(new_turn)
    return redacted
