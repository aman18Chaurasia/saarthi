"""Parametric persona generator for synthetic customers."""
from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import yaml

# Persona parameters
INCOME_RANGES = [
    (8000, 14999, "low"),
    (15000, 29999, "medium"),
    (30000, 74999, "high"),
    (75000, 200000, "very_high"),
]

PURPOSES = {
    "personal_loan": ["home_renovation", "medical", "education", "travel", "debt_consolidation"],
    "home_loan": ["first_home", "second_home", "property_investment"],
    "education_loan": ["engineering", "MBA", "medicine", "study_abroad"],
}

PERSONALITY_TYPES = [
    "cooperative",      # Answers clearly, provides info
    "hesitant",        # Asks questions, needs reassurance
    "objection_prone", # Raises concerns about rates/terms
    "rushed",          # Short responses, wants quick decision
    "detail_oriented", # Asks many clarifying questions
]


def generate_persona(persona_id: int, product: str) -> dict[str, Any]:
    """Generate a single persona with random parameters."""
    income, _, income_level = random.choice(INCOME_RANGES)
    purpose = random.choice(PURPOSES.get(product, ["general"]))
    personality = random.choice(PERSONALITY_TYPES)

    # Determine eligibility
    min_income = {
        "personal_loan": 15000,
        "home_loan": 25000,
        "education_loan": 20000,
    }.get(product, 15000)

    eligible = income >= min_income

    return {
        "persona_id": f"{product}_{persona_id:04d}",
        "product": product,
        "monthly_income_inr": income,
        "income_level": income_level,
        "loan_purpose": purpose,
        "personality_type": personality,
        "expected_outcome": "qualified" if eligible else "not_qualified",
        "age": random.randint(25, 55),
        "has_time": random.choice([True, True, True, False]),  # 75% have time
    }


def generate_batch(product: str, count: int, output_dir: Path) -> None:
    """Generate a batch of personas and save to YAML files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    personas = []
    for i in range(count):
        persona = generate_persona(i, product)
        personas.append(persona)

        # Save individual file
        persona_file = output_dir / f"{persona['persona_id']}.yaml"
        with open(persona_file, "w") as f:
            yaml.dump(persona, f, default_flow_style=False)

    print(f"Generated {count} personas for {product} in {output_dir}")
    return personas


def generate_all_products(count_per_product: int = 50) -> None:
    """Generate personas for all 10 products."""
    base_dir = Path("evals/personas")

    products = [
        "personal_loan", "home_loan", "education_loan", "gold_loan", "credit_card",
        "unsecured_loan", "lap_secured", "commercial_vehicle", "four_wheeler", "msme_business"
    ]

    total = 0
    for product in products:
        product_dir = base_dir / product
        personas = generate_batch(product, count_per_product, product_dir)
        total += len(personas)

    print(f"\n✓ Generated {total} total personas ({count_per_product} per product)")


if __name__ == "__main__":
    generate_all_products(count_per_product=50)
