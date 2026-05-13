"""Compliance guardrail: Presidio PII detection + LLM judge."""
from __future__ import annotations

import logging
import re
from typing import Any

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

logger = logging.getLogger(__name__)

# Indian PII patterns
PAN_PATTERN = re.compile(r'\b[A-Z]{5}\d{4}[A-Z]\b')
AADHAAR_PATTERN = re.compile(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b')
CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b')
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_PATTERN = re.compile(r'\b(?:\+91|0)?[6-9]\d{9}\b')

# Initialize Presidio
_analyzer: AnalyzerEngine | None = None
_anonymizer: AnonymizerEngine | None = None


def get_analyzer() -> AnalyzerEngine:
    """Get singleton Presidio analyzer."""
    global _analyzer
    if _analyzer is None:
        provider = NlpEngineProvider(nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}]
        })
        _analyzer = AnalyzerEngine(nlp_engine=provider.create_engine())
    return _analyzer


def get_anonymizer() -> AnonymizerEngine:
    """Get singleton Presidio anonymizer."""
    global _anonymizer
    if _anonymizer is None:
        _anonymizer = AnonymizerEngine()
    return _anonymizer


async def check_compliance(
    text: str,
    product: str,
    llm_fn: Any | None = None,
) -> dict[str, Any]:
    """Check text for PII and compliance violations.

    Returns:
        {
            "compliant": bool,
            "pii_detected": list[str],
            "violations": list[str]
        }
    """
    analyzer = get_analyzer()

    # Detect PII
    results = analyzer.analyze(
        text=text,
        language="en",
        entities=["PHONE_NUMBER", "EMAIL_ADDRESS", "CREDIT_CARD"]
    )

    pii_types = [r.entity_type for r in results]

    # Simple pattern matching as fallback
    import re
    cc_pattern = r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'
    if re.search(cc_pattern, text):
        pii_types.append("CREDIT_CARD")

    # Simple rules
    violations = []
    if "CREDIT_CARD" in pii_types:
        violations.append("Credit card number detected")

    return {
        "compliant": len(violations) == 0,
        "pii_detected": pii_types,
        "violations": violations
    }


def redact_pii(text: str) -> str:
    """Redact PII from text using regex patterns.

    Returns text with PII replaced by placeholders:
    - PAN → <PAN_REDACTED>
    - Aadhaar → <AADHAAR_REDACTED>
    - Email → <EMAIL_REDACTED>
    - Phone → <PHONE_REDACTED>
    - Credit Card → <CARD_REDACTED>
    """
    if not text:
        return text

    # Redact in order (most specific first)
    redacted = text

    # PAN (format: ABCDE1234F)
    redacted = PAN_PATTERN.sub('<PAN_REDACTED>', redacted)

    # Credit Card (16 digits, before Aadhaar since both are 12-16 digits)
    redacted = CREDIT_CARD_PATTERN.sub('<CARD_REDACTED>', redacted)

    # Aadhaar (12 digits)
    redacted = AADHAAR_PATTERN.sub('<AADHAAR_REDACTED>', redacted)

    # Email
    redacted = EMAIL_PATTERN.sub('<EMAIL_REDACTED>', redacted)

    # Phone
    redacted = PHONE_PATTERN.sub('<PHONE_REDACTED>', redacted)

    return redacted
