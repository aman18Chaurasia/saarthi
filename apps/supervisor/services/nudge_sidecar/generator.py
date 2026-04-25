"""Nudge candidate generator."""
from __future__ import annotations

import json
from dataclasses import dataclass

from llm_client import get_chat_provider

from .router import RouteResult


@dataclass
class NudgeCandidate:
    """Generated nudge suggestion."""

    title: str
    suggestion: str
    priority: int  # 1=high, 2=medium, 3=low


class NudgeGenerator:
    """Generates contextual nudges for agents."""

    OBJECTION_PROMPT = """Customer is objecting or hesitant.

Customer said: "{customer_text}"

Recent context:
{context}

Generate ONE concise response suggestion for the agent (max 30 words).
Make it:
- Empathetic to customer concern
- Addresses the specific objection
- Moves conversation forward

Output JSON: {{"title": "Brief title", "suggestion": "Response text", "priority": 1-3}}
Priority: 1=urgent, 2=important, 3=helpful
"""

    PRODUCT_QUESTION_PROMPT = """Customer asked about product details.

Customer question: "{customer_text}"

Recent context:
{context}

Generate factual answer about the loan product (max 40 words).
Must be:
- Accurate and compliant
- Directly answers question
- Clear and simple

Output JSON: {{"title": "Brief title", "suggestion": "Answer text", "priority": 1-3}}
"""

    COMPLIANCE_ALERT_PROMPT = """COMPLIANCE RISK DETECTED

Agent said something potentially non-compliant: "{agent_text}"

Issue: This may violate lending regulations (false guarantees, pressure tactics, etc.)

Generate immediate alert for supervisor:
- Flag the specific issue
- Suggest corrective action
- Mark as high priority

Output JSON: {{"title": "⚠️ Compliance Alert", "suggestion": "Alert text", "priority": 1}}
"""

    async def generate(
        self,
        route_result: RouteResult,
        context: list[dict],
    ) -> NudgeCandidate:
        """Generate nudge based on route.

        Args:
            route_result: Classification result
            context: Recent conversation turns

        Returns:
            NudgeCandidate with suggestion
        """
        if route_result.route == "OBJECTION":
            return await self._generate_objection_nudge(context)

        elif route_result.route == "PRODUCT_QUESTION":
            return await self._generate_product_nudge(context)

        elif route_result.route == "COMPLIANCE_RISK":
            return await self._generate_compliance_alert(context)

        else:
            # Fallback for NONE route
            return NudgeCandidate(
                title="No action needed",
                suggestion="Conversation flowing normally",
                priority=3,
            )

    async def _generate_objection_nudge(self, context: list[dict]) -> NudgeCandidate:
        """Generate nudge for customer objection."""
        customer_text = self._get_last_customer_text(context)
        context_str = self._format_context(context)

        llm = get_chat_provider()

        response_text = await llm.chat([
            {
                "role": "user",
                "content": self.OBJECTION_PROMPT.format(
                    customer_text=customer_text,
                    context=context_str,
                ),
            }
        ])

        result = json.loads(response_text)
        return NudgeCandidate(**result)

    async def _generate_product_nudge(self, context: list[dict]) -> NudgeCandidate:
        """Generate nudge for product question."""
        customer_text = self._get_last_customer_text(context)
        context_str = self._format_context(context)

        llm = get_chat_provider()

        response_text = await llm.chat([
            {
                "role": "user",
                "content": self.PRODUCT_QUESTION_PROMPT.format(
                    customer_text=customer_text,
                    context=context_str,
                ),
            }
        ])

        result = json.loads(response_text)
        return NudgeCandidate(**result)

    async def _generate_compliance_alert(self, context: list[dict]) -> NudgeCandidate:
        """Generate compliance alert."""
        agent_text = self._get_last_agent_text(context)
        context_str = self._format_context(context)

        llm = get_chat_provider()

        response_text = await llm.chat([
            {
                "role": "user",
                "content": self.COMPLIANCE_ALERT_PROMPT.format(
                    agent_text=agent_text,
                    context=context_str,
                ),
            }
        ])

        result = json.loads(response_text)
        return NudgeCandidate(**result)

    def _get_last_customer_text(self, context: list[dict]) -> str:
        """Extract last customer turn text."""
        for turn in reversed(context):
            if turn["speaker"] == "customer":
                return turn["text"]
        return ""

    def _get_last_agent_text(self, context: list[dict]) -> str:
        """Extract last agent turn text."""
        for turn in reversed(context):
            if turn["speaker"] == "agent":
                return turn["text"]
        return ""

    def _format_context(self, context: list[dict]) -> str:
        """Format context for prompt."""
        lines = []
        for turn in context[-5:]:
            speaker = turn["speaker"].capitalize()
            text = turn["text"]
            lines.append(f"{speaker}: {text}")
        return "\n".join(lines) if lines else "(no context)"
