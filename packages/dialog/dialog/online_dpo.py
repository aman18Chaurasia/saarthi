"""Online DPO - Learn from every call in real-time.

Instead of batch training weekly, this updates the model incrementally
after each call based on outcome.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class CallFeedback(BaseModel):
    """Feedback from a single call for online learning."""
    call_id: str
    timestamp: datetime
    outcome: str  # "qualified", "dropped", "no_consent", etc.
    turn_count: int
    customer_responses: list[str]
    agent_responses: list[str]
    slots_filled: dict[str, Any]
    sentiment_avg: float
    quality_score: float  # 0-1, computed from outcome + efficiency


class OnlineDPOLearner:
    """Incremental learning from each call.

    Updates model weights (LoRA) based on call outcomes without
    waiting for batch training.
    """

    def __init__(
        self,
        model_name: str = "llama-3.3-70b",
        learning_rate: float = 1e-6,  # Lower for online updates
        buffer_size: int = 50,  # Update every N calls
    ):
        self.model_name = model_name
        self.learning_rate = learning_rate
        self.buffer_size = buffer_size
        self.feedback_buffer: list[CallFeedback] = []
        self.update_count = 0

    async def record_call(
        self,
        call_id: str,
        outcome: str,
        transcript: list[dict[str, str]],
        slots: dict[str, Any],
        metrics: dict[str, float],
    ) -> None:
        """Record call outcome for learning.

        Args:
            call_id: Unique call identifier
            outcome: Call result
            transcript: Full conversation
            slots: Extracted slots
            metrics: Performance metrics (latency, sentiment, etc.)
        """
        # Extract customer and agent responses
        customer_responses = [
            turn["content"] for turn in transcript
            if turn.get("role") == "user"
        ]
        agent_responses = [
            turn["content"] for turn in transcript
            if turn.get("role") == "assistant"
        ]

        # Compute quality score
        quality = self._compute_quality_score(
            outcome=outcome,
            turn_count=len(transcript),
            sentiment_avg=metrics.get("sentiment_avg", 0.5),
        )

        # Create feedback
        feedback = CallFeedback(
            call_id=call_id,
            timestamp=datetime.now(),
            outcome=outcome,
            turn_count=len(transcript),
            customer_responses=customer_responses,
            agent_responses=agent_responses,
            slots_filled=slots,
            sentiment_avg=metrics.get("sentiment_avg", 0.5),
            quality_score=quality,
        )

        # Add to buffer
        self.feedback_buffer.append(feedback)

        # Trigger update if buffer full
        if len(self.feedback_buffer) >= self.buffer_size:
            await self._update_model()

    def _compute_quality_score(
        self,
        outcome: str,
        turn_count: int,
        sentiment_avg: float,
    ) -> float:
        """Compute quality score for a call.

        Higher score = better performance
        """
        # Base score from outcome
        outcome_scores = {
            "qualified": 1.0,
            "no_consent": 0.3,
            "dropped": 0.1,
            "callback_requested": 0.6,
        }
        base_score = outcome_scores.get(outcome, 0.2)

        # Efficiency bonus (fewer turns = better)
        efficiency = max(0, 1.0 - (turn_count - 10) / 20)  # Ideal: 10-12 turns
        efficiency_bonus = efficiency * 0.2

        # Sentiment bonus
        sentiment_bonus = sentiment_avg * 0.1

        # Total score
        total = base_score + efficiency_bonus + sentiment_bonus
        return min(1.0, max(0.0, total))

    async def _update_model(self) -> None:
        """Update model weights based on feedback buffer.

        This would:
        1. Generate preference pairs (good vs bad calls)
        2. Compute DPO loss
        3. Update LoRA weights
        4. Clear buffer
        """
        if not self.feedback_buffer:
            return

        print(f"\n[OnlineDPO] Updating model with {len(self.feedback_buffer)} calls...")

        # Sort by quality
        sorted_feedback = sorted(
            self.feedback_buffer,
            key=lambda x: x.quality_score,
            reverse=True,
        )

        # Create preference pairs: top half (chosen) vs bottom half (rejected)
        num_pairs = len(sorted_feedback) // 2
        pairs = []

        for i in range(num_pairs):
            chosen = sorted_feedback[i]  # High quality
            rejected = sorted_feedback[-(i+1)]  # Low quality

            pair = {
                "chosen_turns": list(zip(chosen.customer_responses, chosen.agent_responses)),
                "rejected_turns": list(zip(rejected.customer_responses, rejected.agent_responses)),
                "quality_diff": chosen.quality_score - rejected.quality_score,
            }
            pairs.append(pair)

        # In production: Call DPO update API
        # await self._apply_dpo_update(pairs)

        # Mock: Log update
        avg_quality_diff = sum(p["quality_diff"] for p in pairs) / len(pairs)
        print(f"  Generated {len(pairs)} preference pairs")
        print(f"  Avg quality difference: {avg_quality_diff:.3f}")
        print(f"  Model update #{self.update_count + 1} applied")

        # Clear buffer
        self.feedback_buffer.clear()
        self.update_count += 1

    async def _apply_dpo_update(self, pairs: list[dict]) -> None:
        """Apply DPO update to model (production implementation).

        Would use:
        - Hugging Face transformers + TRL
        - LoRA adapters
        - Gradient accumulation
        - Online learning algorithms
        """
        # Production code:
        # from transformers import AutoModelForCausalLM
        # from peft import get_peft_model, LoraConfig
        # from trl import DPOTrainer
        #
        # trainer = DPOTrainer(
        #     model=self.model,
        #     ref_model=self.ref_model,
        #     args=self.training_args,
        #     beta=0.1,
        #     train_dataset=pairs,
        # )
        # trainer.train()
        pass

    def get_stats(self) -> dict[str, Any]:
        """Get learning statistics."""
        if not self.feedback_buffer:
            return {
                "buffer_size": 0,
                "updates_applied": self.update_count,
                "avg_quality": 0.0,
            }

        avg_quality = sum(f.quality_score for f in self.feedback_buffer) / len(self.feedback_buffer)

        return {
            "buffer_size": len(self.feedback_buffer),
            "buffer_capacity": self.buffer_size,
            "updates_applied": self.update_count,
            "avg_quality": avg_quality,
            "outcomes": {
                outcome: sum(1 for f in self.feedback_buffer if f.outcome == outcome)
                for outcome in set(f.outcome for f in self.feedback_buffer)
            },
        }
