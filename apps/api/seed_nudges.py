"""Seed nudge templates for all 10 BFSI products."""
from __future__ import annotations

import asyncio
from datetime import datetime

from db import AsyncSessionLocal
from models.nudge import NudgeTemplate

PRODUCTS = [
    "personal_loan",
    "home_loan",
    "education_loan",
    "gold_loan",
    "credit_card",
    "unsecured_loan",
    "loan_against_property",
    "commercial_vehicle_loan",
    "four_wheeler_loan",
    "msme_business_loan",
]

# Template definitions: product -> trigger_type -> templates
NUDGE_TEMPLATES = {
    "personal_loan": {
        "product_fact": [
            {
                "trigger_keywords": ["interest", "rate", "percentage"],
                "title": "Interest Rate Details",
                "suggestion": "Our Personal Loan interest rates start from 10.5% p.a. for salaried customers with good credit scores.",
            },
            {
                "trigger_keywords": ["tenure", "duration", "period"],
                "title": "Loan Tenure Options",
                "suggestion": "We offer flexible repayment tenure from 12 to 60 months. Longer tenure means lower EMI.",
            },
            {
                "trigger_keywords": ["documents", "papers", "required"],
                "title": "Documentation Required",
                "suggestion": "For Personal Loan: PAN, Aadhaar, last 3 months salary slips, and 6 months bank statement.",
            },
        ],
        "objection": [
            {
                "trigger_keywords": ["expensive", "costly", "high rate"],
                "title": "Handle Rate Objection",
                "suggestion": "Our rates are competitive compared to market. Plus, we offer special discounts for existing customers and high CIBIL scores.",
            },
            {
                "trigger_keywords": ["need time", "think", "discuss"],
                "title": "Handle Delay",
                "suggestion": "I understand. This offer is valid for 7 days. Can I schedule a callback tomorrow at your convenient time?",
            },
        ],
        "eligibility": [
            {
                "trigger_keywords": ["qualify", "eligible", "minimum"],
                "title": "Eligibility Criteria",
                "suggestion": "Minimum requirements: Age 21-60, monthly income ₹25,000+, and CIBIL score 700+.",
            },
        ],
    },
    "home_loan": {
        "product_fact": [
            {
                "trigger_keywords": ["interest", "rate"],
                "title": "Home Loan Rates",
                "suggestion": "Home Loan rates start from 8.5% p.a. We also have special rates for women applicants - 0.05% discount.",
            },
            {
                "trigger_keywords": ["down payment", "upfront"],
                "title": "Down Payment",
                "suggestion": "We finance up to 90% of property value. Minimum 10% down payment required from your side.",
            },
        ],
        "objection": [
            {
                "trigger_keywords": ["processing fee", "charges"],
                "title": "Fee Waiver",
                "suggestion": "Processing fee is 0.5% of loan amount. For loans above ₹50 lakhs, we can reduce it to 0.25%.",
            },
        ],
    },
    "education_loan": {
        "product_fact": [
            {
                "trigger_keywords": ["interest", "rate"],
                "title": "Education Loan Rates",
                "suggestion": "Education Loan rates start from 9.5% p.a. Interest payment can be deferred until course completion.",
            },
            {
                "trigger_keywords": ["coverage", "covers", "expenses"],
                "title": "Loan Coverage",
                "suggestion": "We cover tuition fees, hostel, books, equipment, and travel expenses for studying abroad.",
            },
        ],
    },
    "gold_loan": {
        "product_fact": [
            {
                "trigger_keywords": ["rate", "interest"],
                "title": "Gold Loan Rates",
                "suggestion": "Gold Loan starting at 7.5% p.a. Lowest rates in the market. Instant disbursal within 30 minutes.",
            },
            {
                "trigger_keywords": ["valuation", "purity"],
                "title": "Gold Valuation",
                "suggestion": "We provide up to 75% of gold value. Free purity testing using XRF machine.",
            },
        ],
    },
    "credit_card": {
        "product_fact": [
            {
                "trigger_keywords": ["fee", "annual", "charges"],
                "title": "Card Fees",
                "suggestion": "Lifetime free credit card for first year. ₹500 annual fee from 2nd year, waived if annual spend >₹1.5L.",
            },
            {
                "trigger_keywords": ["reward", "cashback", "points"],
                "title": "Rewards Program",
                "suggestion": "Earn 2% cashback on all online spends, 5% on groceries and dining. No capping.",
            },
        ],
    },
    "unsecured_loan": {
        "product_fact": [
            {
                "trigger_keywords": ["collateral", "security"],
                "title": "No Collateral",
                "suggestion": "This is an unsecured loan - no collateral or guarantor needed. Approval based on income and credit score.",
            },
        ],
    },
    "loan_against_property": {
        "product_fact": [
            {
                "trigger_keywords": ["ltv", "loan to value"],
                "title": "Loan to Value Ratio",
                "suggestion": "We offer up to 65% of property market value. Residential properties get better LTV than commercial.",
            },
        ],
    },
    "commercial_vehicle_loan": {
        "product_fact": [
            {
                "trigger_keywords": ["margin", "down payment"],
                "title": "Margin Money",
                "suggestion": "We finance up to 90% of vehicle on-road price. Minimum 10% margin money required.",
            },
        ],
    },
    "four_wheeler_loan": {
        "product_fact": [
            {
                "trigger_keywords": ["rate", "interest"],
                "title": "Car Loan Rates",
                "suggestion": "Car Loan rates from 8.5% p.a. Special festive offers available - check with manager.",
            },
        ],
    },
    "msme_business_loan": {
        "product_fact": [
            {
                "trigger_keywords": ["limit", "amount"],
                "title": "Loan Amount",
                "suggestion": "MSME Business Loan from ₹1 lakh to ₹50 lakhs. Working capital or term loan - both available.",
            },
        ],
    },
}


async def seed_nudge_templates() -> None:
    """Seed nudge templates for all products."""
    async with AsyncSessionLocal() as session:
        # Check if templates already exist
        from sqlmodel import select
        result = await session.exec(select(NudgeTemplate).limit(1))
        existing = result.first()
        if existing:
            print("Nudge templates already exist. Skipping seed.")
            return

        templates_created = 0
        for product, categories in NUDGE_TEMPLATES.items():
            for trigger_type, templates in categories.items():
                for template_data in templates:
                    template = NudgeTemplate(
                        product=product,
                        trigger_type=trigger_type,
                        trigger_keywords=template_data["trigger_keywords"],
                        title=template_data["title"],
                        suggestion=template_data["suggestion"],
                        priority="medium",
                        confidence_threshold=0.7,
                        enabled=True,
                        metadata={"source": "seed", "version": "1.0"},
                    )
                    session.add(template)
                    templates_created += 1

        await session.commit()
        print(f"✓ Created {templates_created} nudge templates across {len(PRODUCTS)} products")


if __name__ == "__main__":
    asyncio.run(seed_nudge_templates())
