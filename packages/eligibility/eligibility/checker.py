"""Eligibility checker with Neo4j KG backend and fallback rules."""
from __future__ import annotations

import logging
from typing import Any

from neo4j.exceptions import Neo4jError, ServiceUnavailable

from .client import get_client
from .schema import EligibilityResult, ProductRule

logger = logging.getLogger(__name__)


# Fallback rules when Neo4j is unavailable
FALLBACK_RULES = {
    "personal_loan": {"min_income_inr": 15000},
    "home_loan": {"min_income_inr": 25000},
    "education_loan": {"min_income_inr": 20000},
    "gold_loan": {"min_income_inr": 10000},
    "credit_card": {"min_income_inr": 20000},
    "unsecured_loan": {"min_income_inr": 15000},
    "lap_secured": {"min_income_inr": 30000},
    "commercial_vehicle": {"min_income_inr": 25000},
    "four_wheeler": {"min_income_inr": 20000},
    "msme_business": {"min_revenue_inr": 50000},
}


async def check_eligibility(
    product_id: str,
    monthly_income_inr: int | None = None,
    monthly_revenue_inr: int | None = None,
    **kwargs: Any,
) -> EligibilityResult:
    """Check eligibility for a product using Neo4j rules with fallback.

    Args:
        product_id: Product identifier (e.g., "personal_loan")
        monthly_income_inr: Monthly income in INR
        monthly_revenue_inr: Monthly business revenue (for MSME)
        **kwargs: Additional product-specific slots

    Returns:
        EligibilityResult with eligible flag, reasons, and source
    """
    # Try Neo4j first
    try:
        client = get_client()
        rules_data = await client.get_product_rules(product_id)

        if not rules_data:
            # No rules found in Neo4j, use fallback
            return await _check_with_fallback(product_id, monthly_income_inr, monthly_revenue_inr)

        # Parse rules
        rules = [ProductRule(**rule) for rule in rules_data]

        # Evaluate rules
        reasons: list[str] = []
        eligible = True

        for rule in rules:
            if rule.rule_type == "income_threshold":
                if monthly_income_inr is None:
                    eligible = False
                    reasons.append("Monthly income not provided")
                    continue

                if rule.operator == "gte" and monthly_income_inr < rule.threshold_value:
                    eligible = False
                    reasons.append(rule.error_message or f"Income below threshold: ₹{rule.threshold_value}")
                elif rule.operator == "lte" and monthly_income_inr > rule.threshold_value:
                    eligible = False
                    reasons.append(rule.error_message or f"Income above threshold: ₹{rule.threshold_value}")

            elif rule.rule_type == "revenue_threshold":
                if monthly_revenue_inr is None:
                    eligible = False
                    reasons.append("Monthly revenue not provided")
                    continue

                if rule.operator == "gte" and monthly_revenue_inr < rule.threshold_value:
                    eligible = False
                    reasons.append(rule.error_message or f"Revenue below threshold: ₹{rule.threshold_value}")

        return EligibilityResult(
            eligible=eligible,
            reasons=reasons if reasons else ["All eligibility criteria met"],
            source="neo4j",
            matched_rules=len(rules)
        )

    except (Neo4jError, ServiceUnavailable) as e:
        logger.warning(f"Neo4j unavailable for {product_id}: {e}. Using fallback rules.")
        return await _check_with_fallback(product_id, monthly_income_inr, monthly_revenue_inr)
    except Exception as e:
        logger.error(f"Unexpected error checking eligibility for {product_id}: {e}")
        return await _check_with_fallback(product_id, monthly_income_inr, monthly_revenue_inr)


async def _check_with_fallback(
    product_id: str,
    monthly_income_inr: int | None,
    monthly_revenue_inr: int | None,
) -> EligibilityResult:
    """Apply hardcoded fallback rules when Neo4j is down."""
    if product_id not in FALLBACK_RULES:
        return EligibilityResult(
            eligible=False,
            reasons=[f"Unknown product: {product_id}"],
            source="fallback",
            matched_rules=0
        )

    fallback = FALLBACK_RULES[product_id]

    # MSME uses revenue, others use income
    if "min_revenue_inr" in fallback:
        if monthly_revenue_inr is None or monthly_revenue_inr < fallback["min_revenue_inr"]:
            return EligibilityResult(
                eligible=False,
                reasons=[f"Minimum monthly revenue ₹{fallback['min_revenue_inr']:,} required (fallback rule)"],
                source="fallback",
                matched_rules=1
            )
    else:
        if monthly_income_inr is None or monthly_income_inr < fallback["min_income_inr"]:
            return EligibilityResult(
                eligible=False,
                reasons=[f"Minimum monthly income ₹{fallback['min_income_inr']:,} required (fallback rule)"],
                source="fallback",
                matched_rules=1
            )

    return EligibilityResult(
        eligible=True,
        reasons=["Fallback rule passed"],
        source="fallback",
        matched_rules=1
    )
