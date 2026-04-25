from __future__ import annotations

from typing import Any

_PRIMARY_SLOT_FIELDS: dict[str, tuple[str, ...]] = {
    "commercial_vehicle": ("monthly_income_inr",),
    "credit_card": ("monthly_income_inr",),
    "education_loan": ("monthly_income_inr",),
    "four_wheeler": ("monthly_income_inr",),
    "gold_loan": ("monthly_income_inr",),
    "home_loan": ("monthly_income_inr",),
    "lap_secured": ("monthly_income_inr",),
    "msme_business": ("monthly_revenue_inr",),
    "personal_loan": ("monthly_income_inr",),
    "unsecured_loan": ("monthly_income_inr",),
}

_FOLLOWUP_SLOT_FIELDS: dict[str, tuple[str, ...]] = {
    "commercial_vehicle": ("vehicle_type", "vehicle_price_inr"),
    "credit_card": ("monthly_spending_inr", "existing_cards_count"),
    "education_loan": ("course_name", "institution_name", "course_duration_years"),
    "four_wheeler": ("car_model", "car_price_inr"),
    "gold_loan": ("gold_weight_grams", "gold_purity_karats"),
    "home_loan": ("property_value_inr", "city", "property_type"),
    "lap_secured": ("property_value_inr", "property_type"),
    "msme_business": ("business_purpose",),
    "personal_loan": ("loan_purpose",),
    "unsecured_loan": ("loan_purpose",),
}

_FOLLOWUP_MIN_REQUIRED: dict[str, int] = {
    "commercial_vehicle": 1,
    "credit_card": 1,
    "education_loan": 1,
    "four_wheeler": 1,
    "gold_loan": 1,
    "home_loan": 1,
    "lap_secured": 1,
    "msme_business": 1,
    "personal_loan": 1,
    "unsecured_loan": 1,
}


def _infer_product(slots: Any) -> str | None:
    module_name = getattr(getattr(slots, "__class__", object), "__module__", "")
    parts = module_name.split(".")
    if len(parts) >= 2 and parts[0] == "dialog":
        return parts[1]
    return None


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    return True


def _slot_values(slots: Any, fields: tuple[str, ...]) -> list[Any]:
    values: list[Any] = []
    for field in fields:
        if isinstance(slots, dict):
            values.append(slots.get(field))
        else:
            values.append(getattr(slots, field, None))
    return values


def _captured_count(slots: Any, fields: tuple[str, ...]) -> int:
    return sum(1 for value in _slot_values(slots, fields) if _has_value(value))


def primary_slot_captured(slots: Any, product: str | None = None) -> bool:
    resolved_product = product or _infer_product(slots)
    if resolved_product is None:
        return False
    fields = _PRIMARY_SLOT_FIELDS.get(resolved_product, ())
    return _captured_count(slots, fields) >= 1


def followup_slot_captured(slots: Any, product: str | None = None) -> bool:
    resolved_product = product or _infer_product(slots)
    if resolved_product is None:
        return False
    fields = _FOLLOWUP_SLOT_FIELDS.get(resolved_product, ())
    min_required = _FOLLOWUP_MIN_REQUIRED.get(resolved_product, 1)
    return _captured_count(slots, fields) >= min_required


def determine_outcome(slots: Any, product: str | None = None) -> str:
    if isinstance(slots, dict):
        outcome = slots.get("outcome")
        consent_given = slots.get("consent_given")
        has_time = slots.get("has_time")
    else:
        outcome = getattr(slots, "outcome", None)
        consent_given = getattr(slots, "consent_given", None)
        has_time = getattr(slots, "has_time", None)

    if outcome:
        return str(outcome)
    if consent_given is False:
        return "no_consent"
    if has_time is False:
        return "dropped"
    if (
        consent_given is True
        and primary_slot_captured(slots, product=product)
        and followup_slot_captured(slots, product=product)
    ):
        return "qualified"
    return "dropped"
