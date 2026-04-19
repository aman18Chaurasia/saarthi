"""Tests for compliance guardrail."""
import pytest
from guardrail.compliance import check_compliance


@pytest.mark.asyncio
async def test_clean_text_is_compliant():
    """Clean text passes compliance."""
    result = await check_compliance(
        text="I need a loan for home renovation",
        product="personal_loan"
    )

    assert result["compliant"] is True
    assert result["pii_detected"] == []
    assert result["violations"] == []


@pytest.mark.asyncio
async def test_credit_card_triggers_violation():
    """Credit card number triggers violation."""
    result = await check_compliance(
        text="My card is 4532-1234-5678-9010",
        product="personal_loan"
    )

    assert result["compliant"] is False
    assert "CREDIT_CARD" in result["pii_detected"]
    assert len(result["violations"]) > 0
