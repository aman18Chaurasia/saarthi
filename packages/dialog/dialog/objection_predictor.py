"""Proactive Objection Predictor and Handler.

Predicts likely objections based on customer profile and conversation state,
then preemptively addresses them before customer raises them.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class PredictedObjection(BaseModel):
    """A predicted customer objection."""
    objection_type: str  # "affordability", "interest_rate", "documents", etc.
    probability: float  # 0-1
    preemptive_message: str  # What to say to address it proactively
    trigger_condition: str  # When to use this


class ObjectionPredictor:
    """Predicts and preemptively handles customer objections."""

    def __init__(self, llm_fn: Any | None = None):
        """Initialize objection predictor.

        Args:
            llm_fn: Optional LLM function for advanced prediction
        """
        self.llm_fn = llm_fn

        # Objection templates
        self.objection_templates = {
            "affordability": {
                "indicators": ["low_income", "price_sensitive"],
                "preemptive": "The best part? EMI starts at just ₹2,000/month — very affordable.",
                "reactive": "I understand your concern. Let me show you our most affordable options...",
            },
            "interest_rate": {
                "indicators": ["rate_sensitive", "comparing_products"],
                "preemptive": "We offer competitive rates starting at 9.5% — among the lowest in the market.",
                "reactive": "Our rates are very competitive. Starting at 9.5%, it's one of the best you'll find.",
            },
            "documents": {
                "indicators": ["unfamiliar_with_process", "first_time"],
                "preemptive": "The process is very simple — just Aadhaar, PAN, and last 3 months salary slips.",
                "reactive": "Don't worry, documentation is minimal. Just basic ID and income proof.",
            },
            "time_commitment": {
                "indicators": ["busy", "impatient"],
                "preemptive": "This won't take long — just 2 minutes to qualify, and we handle everything else.",
                "reactive": "I know you're busy. The qualifying process takes just 2 minutes.",
            },
            "trust": {
                "indicators": ["first_call", "skeptical_tone"],
                "preemptive": "We're RBI-approved and have helped over 10,000 customers get loans.",
                "reactive": "We're a legitimate, RBI-approved lender. You can verify our credentials anytime.",
            },
        }

    async def predict_objections(
        self,
        customer_profile: dict[str, Any],
        current_slots: dict[str, Any],
        conversation_stage: str,
    ) -> list[PredictedObjection]:
        """Predict likely objections based on context.

        Args:
            customer_profile: Customer history and preferences
            current_slots: Currently filled slots
            conversation_stage: Current dialog node

        Returns:
            List of predicted objections sorted by probability
        """
        predictions = []

        # Income-based predictions
        monthly_income = current_slots.get("monthly_income_inr", 0)
        if monthly_income > 0 and monthly_income < 25000:
            predictions.append(PredictedObjection(
                objection_type="affordability",
                probability=0.8,
                preemptive_message=self.objection_templates["affordability"]["preemptive"],
                trigger_condition="after_income_collected",
            ))

        # Profile-based predictions
        if "interest_rate" in customer_profile.get("objection_patterns", []):
            predictions.append(PredictedObjection(
                objection_type="interest_rate",
                probability=0.9,  # They've objected before
                preemptive_message=self.objection_templates["interest_rate"]["preemptive"],
                trigger_condition="before_qualifying",
            ))

        if customer_profile.get("total_calls", 0) == 0:
            # First-time caller - might have trust concerns
            predictions.append(PredictedObjection(
                objection_type="trust",
                probability=0.6,
                preemptive_message=self.objection_templates["trust"]["preemptive"],
                trigger_condition="during_opener",
            ))

        # Stage-based predictions
        if conversation_stage == "consent":
            predictions.append(PredictedObjection(
                objection_type="documents",
                probability=0.7,
                preemptive_message=self.objection_templates["documents"]["preemptive"],
                trigger_condition="before_consent_ask",
            ))

        # Sort by probability
        predictions.sort(key=lambda x: x.probability, reverse=True)
        return predictions

    def should_preempt(
        self,
        objection: PredictedObjection,
        current_stage: str,
    ) -> bool:
        """Determine if we should preemptively address this objection now.

        Args:
            objection: Predicted objection
            current_stage: Current conversation stage

        Returns:
            True if should address proactively now
        """
        # Only preempt high-probability objections
        if objection.probability < 0.7:
            return False

        # Check if trigger condition matches current stage
        trigger_mapping = {
            "during_opener": ["opener", "identity_confirm"],
            "before_qualifying": ["identity_confirm"],
            "after_income_collected": ["qualify"],
            "before_consent_ask": ["consent"],
        }

        allowed_stages = trigger_mapping.get(objection.trigger_condition, [])
        return current_stage in allowed_stages

    def handle_reactive_objection(
        self,
        customer_text: str,
    ) -> tuple[bool, str, str]:
        """Detect and handle objection from customer utterance.

        Args:
            customer_text: What customer said

        Returns:
            (is_objection, objection_type, response_message)
        """
        text_lower = customer_text.lower()

        # Pattern matching for objections
        for objection_type, template in self.objection_templates.items():
            keywords = self._get_keywords(objection_type)

            if any(kw in text_lower for kw in keywords):
                return (
                    True,
                    objection_type,
                    template["reactive"]
                )

        return False, "", ""

    def _get_keywords(self, objection_type: str) -> list[str]:
        """Get keywords that indicate an objection type."""
        keyword_map = {
            "affordability": [
                "expensive", "costly", "afford", "budget", "too much",
                "can't pay", "mahanga", "costly hai"
            ],
            "interest_rate": [
                "interest", "rate", "high rate", "ब्याज", "zyada rate"
            ],
            "documents": [
                "documents", "paperwork", "proof", "kaagaz", "papers"
            ],
            "time_commitment": [
                "busy", "no time", "later", "abhi nahi", "time nahi"
            ],
            "trust": [
                "real", "fake", "scam", "fraud", "trust", "legitimate",
                "asli hai", "bharosa"
            ],
        }
        return keyword_map.get(objection_type, [])

    async def get_preemptive_script_addition(
        self,
        current_stage: str,
        customer_profile: dict[str, Any],
        current_slots: dict[str, Any],
    ) -> str:
        """Get text to add to agent's response for preemptive handling.

        Args:
            current_stage: Current dialog node
            customer_profile: Customer history
            current_slots: Current slot values

        Returns:
            Additional text to append to agent response (or empty string)
        """
        # Predict objections
        predictions = await self.predict_objections(
            customer_profile,
            current_slots,
            current_stage,
        )

        # Find objection to preempt
        for objection in predictions:
            if self.should_preempt(objection, current_stage):
                return " " + objection.preemptive_message

        return ""


# ============================================================================
# USAGE EXAMPLE
# ============================================================================
"""
# In dialog nodes:

predictor = ObjectionPredictor()

# During qualify node, after collecting income:
preemptive_text = await predictor.get_preemptive_script_addition(
    current_stage="qualify",
    customer_profile=customer_profile,
    current_slots=state.slots.model_dump(),
)

# Add to agent response
agent_response = base_response + preemptive_text


# When customer says something:
is_objection, obj_type, response = predictor.handle_reactive_objection(
    customer_text=state.asr_text
)

if is_objection:
    # Route to objection handler
    agent_response = response
"""
