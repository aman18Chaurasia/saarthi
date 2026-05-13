"""Preference pair collector for RLAIF training.

Collects pairwise preferences between agent responses for DPO training.
Uses LLM-as-judge to automatically label which response is better.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DialogTurn(BaseModel):
    """Single dialog turn (customer + agent pair)."""
    customer_utterance: str
    agent_response: str
    node_name: str
    turn_index: int


class PreferencePair(BaseModel):
    """Pairwise preference for DPO training."""
    context: list[str]  # Dialog history before this turn
    chosen: str  # Preferred response
    rejected: str  # Rejected response
    reason: str = ""  # Why chosen was preferred
    criteria: str = ""  # Evaluation criteria used
    score_delta: float = 0.0  # How much better chosen vs rejected


class ConversationOutcome(BaseModel):
    """Final outcome of conversation for reward modeling."""
    call_id: str
    product: str
    outcome: Literal["qualified", "not_qualified", "no_consent", "callback_requested", "dropped"]
    success: bool  # Did agent achieve goal?
    turns_count: int
    customer_sentiment_final: Literal["positive", "neutral", "negative", "frustrated"]


async def judge_response_pair(
    context: list[str],
    response_a: str,
    response_b: str,
    llm_fn: Any,
) -> tuple[Literal["A", "B", "tie"], str, float]:
    """Use LLM to judge which response is better.

    Args:
        context: Dialog history
        response_a: First response candidate
        response_b: Second response candidate
        llm_fn: LLM function for judging

    Returns:
        Tuple of (winner, reason, score_delta)
        winner: "A" or "B" or "tie"
        reason: Explanation of preference
        score_delta: Confidence (0.0 to 1.0)
    """
    prompt = f"""You are evaluating two agent responses in a loan qualification dialog.

Context (previous dialog):
{chr(10).join(f"- {line}" for line in context[-3:])}

Response A:
{response_a}

Response B:
{response_b}

Evaluate which response is better based on:
1. Helpfulness - Does it answer customer's question?
2. Naturalness - Does it sound conversational in Hindi/Hinglish?
3. Persuasiveness - Does it move toward qualification/consent?
4. Compliance - No PII leakage, appropriate guardrails

Return JSON:
{{
  "winner": "A" or "B" or "tie",
  "reason": "brief explanation",
  "confidence": 0.0 to 1.0
}}
"""

    try:
        # Call LLM judge
        result = await llm_fn(
            [{"role": "user", "content": prompt}],
            node_name="judge",
            asr_text="",
        )

        winner = result.get("winner", "tie")
        reason = result.get("reason", "No reason provided")
        confidence = float(result.get("confidence", 0.5))

        return (winner, reason, confidence)

    except Exception as e:
        logger.warning(f"LLM judge failed: {e}")
        return ("tie", "Judge error", 0.0)


async def collect_preferences_from_conversation(
    conversation_history: list[DialogTurn],
    alternative_responses: dict[int, list[str]],  # turn_index -> [alt_responses]
    llm_judge_fn: Any,
) -> list[PreferencePair]:
    """Collect preference pairs from single conversation with alternatives.

    Args:
        conversation_history: Actual conversation that happened
        alternative_responses: Alternative agent responses generated for each turn
        llm_judge_fn: LLM function for judging preferences

    Returns:
        List of preference pairs for DPO training
    """
    pairs: list[PreferencePair] = []

    for turn in conversation_history:
        # Skip if no alternatives for this turn
        if turn.turn_index not in alternative_responses:
            continue

        alternatives = alternative_responses[turn.turn_index]
        if not alternatives:
            continue

        # Build context (all utterances before this turn)
        context = []
        for prev_turn in conversation_history:
            if prev_turn.turn_index < turn.turn_index:
                context.append(f"Customer: {prev_turn.customer_utterance}")
                context.append(f"Agent: {prev_turn.agent_response}")

        context.append(f"Customer: {turn.customer_utterance}")

        # Compare actual response vs each alternative
        for alt_response in alternatives:
            winner, reason, confidence = await judge_response_pair(
                context,
                turn.agent_response,  # Response A (what was actually said)
                alt_response,  # Response B (alternative)
                llm_judge_fn,
            )

            # Create preference pair
            if winner == "A":
                pair = PreferencePair(
                    context=context,
                    chosen=turn.agent_response,
                    rejected=alt_response,
                    reason=reason,
                    score_delta=confidence,
                )
                pairs.append(pair)
            elif winner == "B":
                pair = PreferencePair(
                    context=context,
                    chosen=alt_response,
                    rejected=turn.agent_response,
                    reason=reason,
                    score_delta=confidence,
                )
                pairs.append(pair)
            # Skip ties

    return pairs


def save_preference_dataset(
    pairs: list[PreferencePair],
    output_path: Path | str,
) -> None:
    """Save preference pairs to JSONL for DPO training.

    Format compatible with HuggingFace TRL DPOTrainer.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for pair in pairs:
            # Convert to TRL DPO format
            dpo_example = {
                "prompt": "\n".join(pair.context),
                "chosen": pair.chosen,
                "rejected": pair.rejected,
            }
            f.write(json.dumps(dpo_example, ensure_ascii=False) + "\n")

    print(f"[OK] Saved {len(pairs)} preference pairs to {output_path}")


if __name__ == "__main__":
    # Demo: create sample preference pair
    sample_context = [
        "Customer: Mujhe personal loan chahiye",
        "Agent: Theek hai, aapki monthly salary kitni hai?",
        "Customer: 50000 hai",
    ]

    sample_chosen = "Achha, 50000 monthly income. Aapko kitni loan amount chahiye?"
    sample_rejected = "Okay. So what is the amount you need?"  # English = less natural

    pair = PreferencePair(
        context=sample_context,
        chosen=sample_chosen,
        rejected=sample_rejected,
        reason="Chosen maintains Hinglish tone, more natural for customer",
        score_delta=0.8,
    )

    # Save sample dataset
    save_preference_dataset([pair], Path("preference_demo.jsonl"))
    print("Demo preference pair saved")
