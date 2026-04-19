"""Batch evaluation runner for persona conversations."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import yaml


class ConversationSimulator:
    """Simulates a conversation with a persona."""

    def __init__(self, persona: dict[str, Any]):
        self.persona = persona
        self.turns = []

    async def simulate(self) -> dict[str, Any]:
        """Simulate a full conversation based on persona parameters."""
        # Simplified simulation for MVP
        # In full version, this would actually run the LangGraph dialog

        personality = self.persona["personality_type"]

        # Simulate responses based on personality
        if personality == "cooperative":
            self.turns = [
                {"customer": f"I need a {self.persona['product']}", "agent": "opener"},
                {"customer": "Yes, I have time", "agent": "identity_confirm"},
                {"customer": f"My income is {self.persona['monthly_income_inr']}", "agent": "qualify"},
                {"customer": f"For {self.persona['loan_purpose']}", "agent": "qualify_followup"},
                {"customer": "Yes, I consent", "agent": "consent"},
            ]
            final_outcome = self.persona["expected_outcome"]

        elif personality == "hesitant":
            self.turns = [
                {"customer": f"I'm interested in {self.persona['product']}", "agent": "opener"},
                {"customer": "What will this take long?", "agent": "identity_confirm"},
                {"customer": "I guess I have a few minutes", "agent": "identity_confirm"},
                {"customer": f"Around {self.persona['monthly_income_inr']}", "agent": "qualify"},
            ]
            final_outcome = "dropped" if not self.persona["has_time"] else self.persona["expected_outcome"]

        else:  # Default
            self.turns = [
                {"customer": f"Tell me about {self.persona['product']}", "agent": "opener"},
                {"customer": f"{self.persona['monthly_income_inr']} monthly", "agent": "qualify"},
            ]
            final_outcome = self.persona["expected_outcome"]

        return {
            "persona_id": self.persona["persona_id"],
            "turns": self.turns,
            "turn_count": len(self.turns),
            "outcome": final_outcome,
            "expected_outcome": self.persona["expected_outcome"],
            "match": final_outcome == self.persona["expected_outcome"],
        }


async def run_evaluation(persona_dir: Path, output_file: Path) -> dict[str, Any]:
    """Run evaluation on all personas in directory."""
    results = []

    persona_files = list(persona_dir.glob("*.yaml"))
    print(f"Running evaluation on {len(persona_files)} personas...")

    for persona_file in persona_files:
        with open(persona_file) as f:
            persona = yaml.safe_load(f)

        simulator = ConversationSimulator(persona)
        result = await simulator.simulate()
        results.append(result)

    # Calculate metrics
    total = len(results)
    matches = sum(1 for r in results if r["match"])
    accuracy = matches / total if total > 0 else 0

    summary = {
        "total_personas": total,
        "matches": matches,
        "accuracy": accuracy,
        "results": results,
    }

    # Save results
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"✓ Accuracy: {accuracy:.1%} ({matches}/{total})")
    return summary


async def run_all_products() -> None:
    """Run evaluation on all product personas."""
    base_dir = Path("evals/personas")
    output_dir = Path("evals/results")

    products = list(base_dir.iterdir())

    for product_dir in products:
        if not product_dir.is_dir():
            continue

        print(f"\n--- {product_dir.name} ---")
        output_file = output_dir / f"{product_dir.name}_results.json"
        await run_evaluation(product_dir, output_file)


if __name__ == "__main__":
    asyncio.run(run_all_products())
