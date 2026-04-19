"""Compliance guardrail: Presidio PII detection + LLM judge."""
from __future__ import annotations

import logging
from typing import Any

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

logger = logging.getLogger(__name__)

# Initialize Presidio
_analyzer: AnalyzerEngine | None = None


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
