"""Main nudge sidecar pipeline.

Orchestrates: context → router → generator → policy → publisher
"""
from __future__ import annotations

from dataclasses import dataclass

from ..context_manager import NudgeContextManager
from .generator import NudgeGenerator
from .policy import NudgePolicy
from .publisher import NudgePublisher
from .router import NudgeRouter


@dataclass
class TranscriptChunk:
    """Incoming transcript chunk."""

    call_id: str
    speaker: str  # "agent" or "customer"
    text: str
    timestamp: float


class NudgeSidecarPipeline:
    """Main nudge processing pipeline."""

    def __init__(self):
        self.context_mgr = NudgeContextManager()
        self.router = NudgeRouter()
        self.generator = NudgeGenerator()
        self.policy = NudgePolicy()
        self.publisher = NudgePublisher()

    async def process(self, chunk: TranscriptChunk) -> None:
        """Process transcript chunk through full pipeline.

        Steps:
        1. Store chunk in context
        2. Only process customer turns
        3. Route classification
        4. Generate candidate nudge
        5. Policy gate
        6. Publish if approved

        Args:
            chunk: Incoming transcript chunk
        """
        # 1. Store in context
        await self.context_mgr.append_turn(
            chunk.call_id,
            chunk.speaker,
            chunk.text,
            chunk.timestamp,
        )

        # 2. Only process customer turns (agent gets nudges for customer responses)
        if chunk.speaker != "customer":
            return

        # 3. Load context
        context = await self.context_mgr.get_context(chunk.call_id)

        # 4. Route classification
        route_result = await self.router.classify(context, chunk.text)

        # Log decision even if NONE
        await self.publisher.publish_decision(
            chunk.call_id,
            {
                "route": route_result.route,
                "confidence": route_result.confidence,
                "customer_text": chunk.text,
            },
        )

        if route_result.route == "NONE":
            await self.publisher.publish_decision(
                chunk.call_id,
                {
                    "route": "NONE",
                    "suppressed": True,
                    "reason": "no_actionable_intent",
                },
            )
            return

        # 5. Generate candidate
        candidate = await self.generator.generate(route_result, context)

        # 6. Policy check
        should_emit, reason = await self.policy.check(
            chunk.call_id,
            candidate,
            route_result.confidence,
        )

        if not should_emit:
            # Log suppression
            await self.publisher.publish_decision(
                chunk.call_id,
                {
                    "route": route_result.route,
                    "suppressed": True,
                    "reason": reason,
                    "candidate_title": candidate.title,
                    "candidate_suggestion": candidate.suggestion,
                    "confidence": route_result.confidence,
                },
            )
            return

        # 7. Emit nudge
        await self.publisher.publish_nudge(
            chunk.call_id,
            {
                "route": route_result.route,
                "title": candidate.title,
                "suggestion": candidate.suggestion,
                "priority": candidate.priority,
                "confidence": route_result.confidence,
                "transcript": chunk.text,
            },
        )

        # Log successful emit
        await self.publisher.publish_decision(
            chunk.call_id,
            {
                "route": route_result.route,
                "suppressed": False,
                "reason": "emitted",
                "nudge_title": candidate.title,
                "confidence": route_result.confidence,
            },
        )
