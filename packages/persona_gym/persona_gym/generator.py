"""Synthetic persona generator for SAARTHI evaluation.

Generates parametric customer personas as YAML files for testing dialog agents.
Each persona includes demographics, loan requirements, objection patterns, etc.
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field


class PersonaDemographics(BaseModel):
    """Customer demographics."""
    age: int = Field(ge=21, le=65)
    gender: Literal["male", "female", "other"]
    occupation: str
    monthly_income_inr: int = Field(ge=15000, le=500000)
    city: str
    marital_status: Literal["single", "married", "divorced", "widowed"]
    dependents: int = Field(ge=0, le=5)


class PersonaLoanRequest(BaseModel):
    """Loan requirements."""
    product: str
    amount_inr: int
    purpose: str
    tenure_months: int = Field(ge=6, le=360)
    existing_loans: int = Field(ge=0, le=3)
    cibil_score: int = Field(ge=300, le=900)


class PersonaBehavior(BaseModel):
    """Conversation behavior patterns."""
    language_preference: Literal["hindi", "english", "hinglish"]
    verbosity: Literal["concise", "moderate", "verbose"]
    cooperation_level: Literal["cooperative", "neutral", "resistant"]
    objection_types: list[str] = Field(default_factory=list)
    question_count: int = Field(ge=0, le=10)  # How many questions they ask
    consent_willingness: Literal["ready", "hesitant", "refuses"]


class Persona(BaseModel):
    """Complete synthetic customer persona."""
    persona_id: str
    demographics: PersonaDemographics
    loan_request: PersonaLoanRequest
    behavior: PersonaBehavior
    scenario_notes: str = ""  # Additional context


# Occupation distributions by income bracket
OCCUPATIONS = {
    "low": ["factory worker", "driver", "security guard", "domestic worker", "retail clerk"],
    "mid": ["teacher", "accountant", "IT support", "sales executive", "nurse"],
    "high": ["software engineer", "doctor", "lawyer", "consultant", "bank manager"],
}

CITIES = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Pune", "Chennai", "Kolkata", "Ahmedabad"]

LOAN_PURPOSES = {
    "personal_loan": ["wedding", "medical emergency", "home renovation", "education", "debt consolidation"],
    "home_loan": ["purchasing new house", "house construction", "home purchase"],
    "education_loan": ["higher studies", "MBA abroad", "engineering degree", "medical college"],
    "gold_loan": ["business working capital", "medical emergency", "wedding expenses"],
    "four_wheeler_loan": ["buying car", "vehicle purchase"],
    "commercial_vehicle_loan": ["buying truck", "transport business", "logistics"],
    "loan_against_property": ["business expansion", "working capital", "debt refinance"],
    "msme_business_loan": ["business expansion", "machinery purchase", "working capital"],
    "credit_card": ["travel rewards", "cashback benefits", "emergency backup"],
    "unsecured_loan": ["wedding", "travel", "medical", "home renovation"],
}

OBJECTION_PATTERNS = [
    "interest_rate_too_high",
    "processing_fee_concerns",
    "tenure_too_long",
    "documentation_burden",
    "cibil_score_concerns",
    "think_about_it",
    "compare_other_banks",
    "need_spouse_approval",
    "not_ready_now",
]


def generate_persona(
    persona_id: str,
    product: str | None = None,
    income_bracket: Literal["low", "mid", "high"] | None = None,
) -> Persona:
    """Generate single synthetic persona.

    Args:
        persona_id: Unique ID for this persona
        product: Product type (random if None)
        income_bracket: Income level (random if None)

    Returns:
        Generated Persona
    """
    if income_bracket is None:
        income_bracket = random.choice(["low", "mid", "high"])

    # Income ranges
    income_ranges = {
        "low": (15000, 35000),
        "mid": (35000, 75000),
        "high": (75000, 500000),
    }
    min_income, max_income = income_ranges[income_bracket]

    # Demographics
    demographics = PersonaDemographics(
        age=random.randint(25, 55),
        gender=random.choice(["male", "female", "other"]),
        occupation=random.choice(OCCUPATIONS[income_bracket]),
        monthly_income_inr=random.randint(min_income, max_income),
        city=random.choice(CITIES),
        marital_status=random.choice(["single", "married", "divorced", "widowed"]),
        dependents=random.randint(0, 3),
    )

    # Loan request
    if product is None:
        product = random.choice(list(LOAN_PURPOSES.keys()))

    # Loan amount scaled to income
    amount_multiplier = random.uniform(2, 8)  # 2-8x monthly income
    amount_inr = int(demographics.monthly_income_inr * amount_multiplier)

    # Tenure based on product
    tenure_map = {
        "personal_loan": (12, 60),
        "home_loan": (120, 360),
        "education_loan": (60, 120),
        "gold_loan": (6, 36),
        "four_wheeler_loan": (24, 84),
        "commercial_vehicle_loan": (36, 84),
        "loan_against_property": (60, 180),
        "msme_business_loan": (12, 60),
        "credit_card": (12, 12),  # Not applicable but keep consistent
        "unsecured_loan": (12, 48),
    }
    min_tenure, max_tenure = tenure_map.get(product, (12, 60))

    loan_request = PersonaLoanRequest(
        product=product,
        amount_inr=amount_inr,
        purpose=random.choice(LOAN_PURPOSES[product]),
        tenure_months=random.randint(min_tenure, max_tenure),
        existing_loans=random.randint(0, 2),
        cibil_score=random.randint(650, 850),  # Weighted toward acceptable range
    )

    # Behavior
    cooperation_dist = [0.6, 0.3, 0.1]  # cooperative, neutral, resistant
    cooperation = random.choices(
        ["cooperative", "neutral", "resistant"],
        weights=cooperation_dist,
    )[0]

    num_objections = random.randint(0, 3)
    objections = random.sample(OBJECTION_PATTERNS, k=min(num_objections, len(OBJECTION_PATTERNS)))

    behavior = PersonaBehavior(
        language_preference=random.choice(["hindi", "english", "hinglish"]),
        verbosity=random.choice(["concise", "moderate", "verbose"]),
        cooperation_level=cooperation,
        objection_types=objections,
        question_count=random.randint(1, 5),
        consent_willingness=random.choice(["ready", "hesitant", "refuses"]),
    )

    scenario_notes = f"{demographics.occupation.title()}, {demographics.age}y, seeking {product} for {loan_request.purpose}"

    return Persona(
        persona_id=persona_id,
        demographics=demographics,
        loan_request=loan_request,
        behavior=behavior,
        scenario_notes=scenario_notes,
    )


def generate_batch(
    count: int,
    output_dir: Path | str,
    product: str | None = None,
) -> list[Persona]:
    """Generate batch of personas and save to YAML files.

    Args:
        count: Number of personas to generate
        output_dir: Directory to save YAML files
        product: Product type filter (None = all products)

    Returns:
        List of generated personas
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    personas = []
    for i in range(count):
        persona_id = f"persona_{i:04d}"
        persona = generate_persona(persona_id, product=product)
        personas.append(persona)

        # Save to YAML
        yaml_path = output_dir / f"{persona_id}.yaml"
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(
                persona.model_dump(),
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

    print(f"[OK] Generated {count} personas in {output_dir}")
    return personas


if __name__ == "__main__":
    # Demo: generate 100 personas across all products
    output_path = Path("persona_gym_output")
    personas = generate_batch(100, output_path)
    print(f"Generated {len(personas)} personas")

    # Stats
    products = {}
    for p in personas:
        products[p.loan_request.product] = products.get(p.loan_request.product, 0) + 1

    print("\nProduct distribution:")
    for product, count in sorted(products.items()):
        print(f"  {product:30} {count:3} personas")
