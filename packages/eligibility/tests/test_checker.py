"""Tests for eligibility checker with fallback."""
import pytest
from eligibility.checker import check_eligibility


@pytest.mark.asyncio
async def test_personal_loan_eligible_with_fallback():
    """Test personal loan eligibility with sufficient income (fallback mode)."""
    result = await check_eligibility(
        product_id="personal_loan",
        monthly_income_inr=20000
    )

    # Should pass with fallback since Neo4j likely not running
    assert result.eligible is True
    assert result.source == "fallback"
    assert result.matched_rules == 1


@pytest.mark.asyncio
async def test_personal_loan_ineligible_low_income():
    """Test personal loan rejection due to low income (fallback mode)."""
    result = await check_eligibility(
        product_id="personal_loan",
        monthly_income_inr=10000  # Below 15000 threshold
    )

    assert result.eligible is False
    assert result.source == "fallback"
    assert "15,000" in result.reasons[0]


@pytest.mark.asyncio
async def test_home_loan_eligible():
    """Test home loan eligibility with sufficient income."""
    result = await check_eligibility(
        product_id="home_loan",
        monthly_income_inr=30000  # Above 25000 threshold
    )

    assert result.eligible is True
    assert result.source == "fallback"


@pytest.mark.asyncio
async def test_home_loan_ineligible_low_income():
    """Test home loan rejection due to low income."""
    result = await check_eligibility(
        product_id="home_loan",
        monthly_income_inr=20000  # Below 25000 threshold
    )

    assert result.eligible is False
    assert "25,000" in result.reasons[0]


@pytest.mark.asyncio
async def test_msme_business_uses_revenue():
    """Test MSME business loan uses revenue threshold."""
    result = await check_eligibility(
        product_id="msme_business",
        monthly_revenue_inr=60000  # Above 50000 threshold
    )

    assert result.eligible is True
    assert result.source == "fallback"


@pytest.mark.asyncio
async def test_msme_business_ineligible_low_revenue():
    """Test MSME rejection due to low revenue."""
    result = await check_eligibility(
        product_id="msme_business",
        monthly_revenue_inr=30000  # Below 50000 threshold
    )

    assert result.eligible is False
    assert "50,000" in result.reasons[0]


@pytest.mark.asyncio
async def test_unknown_product():
    """Test unknown product ID."""
    result = await check_eligibility(
        product_id="unknown_product",
        monthly_income_inr=20000
    )

    assert result.eligible is False
    assert "Unknown product" in result.reasons[0]


@pytest.mark.asyncio
async def test_missing_income():
    """Test eligibility check with missing income."""
    result = await check_eligibility(
        product_id="personal_loan",
        monthly_income_inr=None
    )

    assert result.eligible is False
