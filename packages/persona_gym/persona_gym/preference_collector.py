"""Preference pair collection for RLAIF."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class PreferenceCollector:
    """Collects preference pairs from conversation variants."""

    def __init__(self):
        self.pairs = []

    def add_pair(
        self,
        persona_id: str,
        baseline_conversation: dict[str, Any],
        variant_conversation: dict[str, Any],
        preference: str,  # "baseline" | "variant" | "tie"
        reason: str,
    ) -> None:
        """Add a preference pair."""
        pair = {
            "persona_id": persona_id,
            "baseline": baseline_conversation,
            "variant": variant_conversation,
            "preference": preference,
            "reason": reason,
        }
        self.pairs.append(pair)

    def auto_judge(
        self,
        baseline: dict[str, Any],
        variant: dict[str, Any],
    ) -> tuple[str, str]:
        """Automatically judge which conversation is better."""
        # Simple heuristic-based judging (LLM judge can be added later)

        baseline_score = 0
        variant_score = 0
        reasons = []

        # Shorter conversations are better (more efficient)
        if baseline["turn_count"] < variant["turn_count"]:
            baseline_score += 1
            reasons.append("baseline more efficient")
        elif variant["turn_count"] < baseline["turn_count"]:
            variant_score += 1
            reasons.append("variant more efficient")

        # Matching expected outcome is critical
        if baseline["match"]:
            baseline_score += 3
        if variant["match"]:
            variant_score += 3

        # Determine preference
        if baseline_score > variant_score:
            return "baseline", " | ".join(reasons)
        elif variant_score > baseline_score:
            return "variant", " | ".join(reasons)
        else:
            return "tie", "equal quality"

    def save(self, output_file: Path) -> None:
        """Save preference pairs to JSON."""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump({
                "total_pairs": len(self.pairs),
                "pairs": self.pairs,
            }, f, indent=2)

        print(f"✓ Saved {len(self.pairs)} preference pairs to {output_file}")


def collect_preferences_from_eval(
    baseline_results: Path,
    variant_results: Path,
    output_file: Path,
) -> dict[str, Any]:
    """Collect preferences by comparing baseline vs variant evaluations."""
    with open(baseline_results) as f:
        baseline_data = json.load(f)
    with open(variant_results) as f:
        variant_data = json.load(f)

    collector = PreferenceCollector()

    # Match personas by ID
    baseline_map = {r["persona_id"]: r for r in baseline_data["results"]}
    variant_map = {r["persona_id"]: r for r in variant_data["results"]}

    for persona_id in baseline_map:
        if persona_id not in variant_map:
            continue

        baseline_conv = baseline_map[persona_id]
        variant_conv = variant_map[persona_id]

        preference, reason = collector.auto_judge(baseline_conv, variant_conv)
        collector.add_pair(persona_id, baseline_conv, variant_conv, preference, reason)

    collector.save(output_file)

    # Stats
    prefs = [p["preference"] for p in collector.pairs]
    baseline_wins = prefs.count("baseline")
    variant_wins = prefs.count("variant")
    ties = prefs.count("tie")

    return {
        "total_pairs": len(collector.pairs),
        "baseline_wins": baseline_wins,
        "variant_wins": variant_wins,
        "ties": ties,
        "variant_win_rate": variant_wins / len(collector.pairs) if collector.pairs else 0,
    }
