"""Intent router for nudge classification."""
from __future__ import annotations

import json
from dataclasses import dataclass

from llm_client import get_chat_provider


@dataclass
class RouteResult:
    """Result of intent classification."""

    route: str  # OBJECTION | PRODUCT_QUESTION | COMPLIANCE_RISK | NONE
    confidence: float  # 0.0 to 1.0


class NudgeRouter:
    """Classifies customer turns into actionable intents."""

    SYSTEM_PROMPT = """You are an intent classifier for agent-customer loan conversations.

Classify customer turns into one of these routes:

1. OBJECTION - Customer is hesitant, refusing, or expressing concerns
   Examples:
   - "Interest rate seems high"
   - "I don't think I can afford this"
   - "Let me think about it"

2. PRODUCT_QUESTION - Customer asks about loan details, eligibility, terms
   Examples:
   - "What's the interest rate?"
   - "Do I need collateral?"
   - "How long is the repayment period?"

3. COMPLIANCE_RISK - Agent saying prohibited things (guaranteed approval, pressure tactics)
   Examples:
   - Agent: "100% approval guaranteed"
   - Agent: "You must decide now"
   - Agent: "No credit check needed"

4. NONE - Normal conversation flow, no actionable intent
   Examples:
   - "Yes, I'm interested"
   - "Thank you"
   - "Okay, go ahead"

Return JSON: {"route": "...", "confidence": 0.0-1.0}
"""

    USER_PROMPT_TEMPLATE = """Conversation context (last 5 turns):
{context}

Current customer turn: "{customer_text}"

Classify this customer turn. Output JSON only."""

    async def classify(
        self,
        context: list[dict],
        customer_text: str,
    ) -> RouteResult:
        """Classify customer turn into route.

        Args:
            context: Recent conversation turns
            customer_text: Current customer utterance

        Returns:
            RouteResult with route and confidence
        """
        llm = get_chat_provider()

        # Format context
        context_str = self._format_context(context)

        # Combine system and user into single prompt for json_mode
        full_prompt = f"""{self.SYSTEM_PROMPT}

{self.USER_PROMPT_TEMPLATE.format(context=context_str, customer_text=customer_text)}"""

        # Call LLM - chat() returns string directly
        response_text = await llm.chat([
            {"role": "user", "content": full_prompt}
        ])

        # Parse result
        result = json.loads(response_text)

        return RouteResult(
            route=result.get("route", "NONE"),
            confidence=float(result.get("confidence", 0.0)),
        )

    def _format_context(self, context: list[dict]) -> str:
        """Format context for prompt.

        Args:
            context: List of turn dicts

        Returns:
            Formatted string
        """
        lines = []
        for turn in context[-5:]:  # Last 5 turns
            speaker = turn["speaker"].capitalize()
            text = turn["text"]
            lines.append(f"{speaker}: {text}")

        return "\n".join(lines) if lines else "(no prior context)"
