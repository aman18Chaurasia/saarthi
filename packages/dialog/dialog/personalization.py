"""Per-Customer Learning & Personalization Engine.

Tracks customer preferences, objections, and successful approaches
across multiple calls to personalize future interactions.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class CustomerProfile(BaseModel):
    """Customer learning profile from past interactions."""
    customer_id: str

    # Preferences
    preferred_language_mix: str = "hinglish"  # "hinglish", "english", "hindi"
    communication_style: str = "balanced"  # "formal", "casual", "balanced"
    preferred_pace: str = "normal"  # "fast", "normal", "slow"

    # Behavioral patterns
    objection_patterns: list[str] = []  # ["interest_rate", "affordability", ...]
    successful_hooks: list[str] = []  # ["financial_security", "family_benefit", ...]
    dropout_reasons: list[str] = []  # Why they hung up in past

    # Engagement metrics
    avg_turns_to_qualify: float = 0.0
    avg_frustration_level: float = 0.0
    best_call_time: str | None = None  # "morning", "afternoon", "evening"

    # Risk profile
    risk_tolerance: str = "medium"  # "low", "medium", "high"
    price_sensitivity: float = 0.5  # 0.0-1.0

    # History
    total_calls: int = 0
    qualified_calls: int = 0
    last_call_date: datetime | None = None
    last_call_outcome: str | None = None

    # Products
    products_interested_in: list[str] = []
    products_rejected: list[str] = []


class PersonalizationEngine:
    """Adapts dialog based on customer's learning profile."""

    def __init__(self, db: Any = None):
        """Initialize personalization engine.

        Args:
            db: Database connection for profile persistence
        """
        self.db = db
        self._cache: dict[str, CustomerProfile] = {}

    async def get_profile(self, customer_id: str) -> CustomerProfile:
        """Retrieve customer profile from database or cache.

        Args:
            customer_id: Unique customer identifier

        Returns:
            CustomerProfile with learning data
        """
        # Check cache first
        if customer_id in self._cache:
            return self._cache[customer_id]

        # Load from database
        if self.db:
            profile_data = await self.db.fetch_customer_profile(customer_id)
            if profile_data:
                profile = CustomerProfile(**profile_data)
                self._cache[customer_id] = profile
                return profile

        # New customer - create default profile
        profile = CustomerProfile(customer_id=customer_id)
        self._cache[customer_id] = profile
        return profile

    async def update_profile(
        self,
        customer_id: str,
        call_outcome: str,
        transcript: list[dict[str, str]],
        slots: dict[str, Any],
    ) -> None:
        """Update customer profile based on call results.

        Args:
            customer_id: Customer identifier
            call_outcome: "qualified", "dropped", "no_consent", etc.
            transcript: List of conversation turns
            slots: Extracted slot values
        """
        profile = await self.get_profile(customer_id)

        # Update call counts
        profile.total_calls += 1
        if call_outcome == "qualified":
            profile.qualified_calls += 1
        profile.last_call_date = datetime.now()
        profile.last_call_outcome = call_outcome

        # Extract objections from transcript
        objection_keywords = {
            "expensive": "affordability",
            "costly": "affordability",
            "high interest": "interest_rate",
            "better rate": "interest_rate",
            "not interested": "lack_interest",
            "busy": "timing",
        }

        for turn in transcript:
            if turn.get("role") == "user":
                text_lower = turn.get("content", "").lower()
                for keyword, objection_type in objection_keywords.items():
                    if keyword in text_lower:
                        if objection_type not in profile.objection_patterns:
                            profile.objection_patterns.append(objection_type)

        # Track successful hooks (if call was successful)
        if call_outcome == "qualified":
            loan_purpose = slots.get("loan_purpose")
            if loan_purpose:
                if loan_purpose not in profile.successful_hooks:
                    profile.successful_hooks.append(loan_purpose)

        # Update average metrics
        turn_count = len(transcript)
        if profile.avg_turns_to_qualify == 0:
            profile.avg_turns_to_qualify = turn_count
        else:
            # Moving average
            profile.avg_turns_to_qualify = (
                profile.avg_turns_to_qualify * 0.7 + turn_count * 0.3
            )

        # Persist to database
        if self.db:
            await self.db.update_customer_profile(customer_id, profile.model_dump())

        # Update cache
        self._cache[customer_id] = profile

    def adapt_opener(self, profile: CustomerProfile, product: str) -> str:
        """Adapt opening based on customer history.

        Args:
            profile: Customer learning profile
            product: Product being offered

        Returns:
            Personalized opening guidance
        """
        if profile.total_calls == 0:
            return ""  # First call, use standard approach

        if profile.last_call_outcome == "dropped":
            if "busy" in profile.dropout_reasons:
                return "NOTE: Customer was busy last time. Start by asking if this is a good time."
            if "timing" in profile.objection_patterns:
                return "NOTE: Customer prefers specific times. Ask for preferred callback time."

        if profile.qualified_calls > 0:
            return "NOTE: Customer has qualified before. They're familiar with our process."

        return ""

    def adapt_qualifying_approach(self, profile: CustomerProfile) -> str:
        """Adapt qualifying questions based on past objections.

        Args:
            profile: Customer learning profile

        Returns:
            Guidance for qualifying phase
        """
        if "affordability" in profile.objection_patterns:
            return """
NOTE: Customer previously objected to affordability.
- Lead with LOW EMI amounts
- Mention flexible tenure options upfront
- Example: "EMI starts at just ₹2,000/month"
"""

        if "interest_rate" in profile.objection_patterns:
            return """
NOTE: Customer is rate-sensitive.
- Mention competitive rates early
- Compare with market rates
- Example: "Starting at 9.5% - among the lowest in the market"
"""

        if profile.price_sensitivity > 0.7:
            return """
NOTE: Customer is price-conscious.
- Emphasize value and savings
- Mention special offers/discounts
- Focus on long-term benefits
"""

        return ""

    def should_try_different_product(self, profile: CustomerProfile, current_product: str) -> tuple[bool, str]:
        """Determine if we should suggest a different product.

        Args:
            profile: Customer learning profile
            current_product: Product currently being offered

        Returns:
            (should_suggest, suggested_product)
        """
        # If current product was rejected before
        if current_product in profile.products_rejected:
            # Suggest product they showed interest in
            for product in profile.products_interested_in:
                if product not in profile.products_rejected:
                    return True, product

        # If they qualified for different product before
        if profile.qualified_calls > 0 and profile.products_interested_in:
            preferred = profile.products_interested_in[0]
            if preferred != current_product:
                return True, preferred

        return False, ""

    def get_optimal_call_time(self, profile: CustomerProfile) -> str:
        """Get best time to call customer.

        Args:
            profile: Customer learning profile

        Returns:
            Recommended call time
        """
        if profile.best_call_time:
            return profile.best_call_time

        # Default based on profile
        if profile.communication_style == "formal":
            return "morning"  # Business hours
        elif profile.communication_style == "casual":
            return "evening"  # After work

        return "afternoon"  # Safe default

    def get_language_preference(self, profile: CustomerProfile) -> str:
        """Get customer's preferred language mix.

        Args:
            profile: Customer learning profile

        Returns:
            Language preference guidance
        """
        if profile.preferred_language_mix == "english":
            return "Use more English, less Hindi mixing."
        elif profile.preferred_language_mix == "hindi":
            return "Use more Hindi, customer prefers it."
        else:
            return "Use balanced Hinglish (current approach)."
