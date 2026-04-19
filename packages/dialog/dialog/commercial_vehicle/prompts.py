"""Prompt assembly for the commercial vehicle dialog nodes.

Loads commercial_vehicle.yaml once at module import and builds per-node system prompts.
The YAML is the single source of truth for all agent script text (ADR 0002 §5).

YAML search order:
  1. COMMERCIAL_VEHICLE_YAML env var (absolute path)
  2. packages/scripts/products/commercial_vehicle.yaml relative to repo root
     (derived from this file's __file__ path)
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

# ── YAML loading ──────────────────────────────────────────────────────────────

def _load_yaml() -> dict[str, Any]:
    env_path = os.environ.get("COMMERCIAL_VEHICLE_YAML")
    if env_path:
        return yaml.safe_load(Path(env_path).read_text(encoding="utf-8"))

    # packages/dialog/dialog/personal_loan/prompts.py
    # parents[3] = packages/dialog → parents[3].parent = packages
    repo_packages = Path(__file__).parents[3]
    default_path = repo_packages / "scripts" / "products" / "commercial_vehicle.yaml"
    if default_path.exists():
        return yaml.safe_load(default_path.read_text(encoding="utf-8"))

    raise FileNotFoundError(
        f"commercial_vehicle.yaml not found. Set COMMERCIAL_VEHICLE_YAML env var or "
        f"ensure the file exists at {default_path}"
    )


_SCRIPT: dict[str, Any] = _load_yaml()

# ── Pause marker stripping ────────────────────────────────────────────────────

_PAUSE_RE = re.compile(r"<pause:[^/]*/?>")


def _strip_pauses(text: str) -> str:
    return _PAUSE_RE.sub("", text).strip()


# ── Per-node script text ──────────────────────────────────────────────────────

def _node_text(node_key: str, sub_key: str | None = None) -> str:
    node = _SCRIPT["nodes"][node_key]
    if sub_key:
        node = node[sub_key]
    return _strip_pauses(node["agent"])


_NODE_SCRIPTS: dict[str, str] = {
    "opener":           _node_text("opener"),
    "identity_confirm": _node_text("identity_confirm"),
    "qualify":          _node_text("qualify"),
    "qualify_followup": _node_text("qualify", "follow_up"),
    "consent":          _node_text("consent"),
    "next_step":        _node_text("next_step"),
    "close":            _node_text("close"),
}

_SLOT_GUIDANCE: dict[str, str] = {
    "opener": "No slots to extract. classified_intent should be 'unclear'.",
    "identity_confirm": (
        "Extract: name_confirmed (bool), has_time (bool).\n\n"
        "EXAMPLES:\n"
        "Customer: 'Yes, I have 2 minutes' → {\"name_confirmed\": true, \"has_time\": true}, intent: affirm\n"
        "Customer: 'I'm looking for a loan' → {\"name_confirmed\": true, \"has_time\": true}, intent: affirm\n"
        "Customer: 'Yes this is Rahul speaking' → {\"name_confirmed\": true, \"has_time\": true}, intent: affirm\n"
        "Customer: 'I'm busy right now' → {\"has_time\": false}, intent: deny\n"
        "Customer: 'What?' → {}, intent: unclear\n\n"
        "RULES: has_time=true if customer engages positively OR expresses interest. has_time=false ONLY if explicitly busy."
    ),
    "qualify": (
        "Extract: monthly_income_inr (integer).\n\n"
        "EXAMPLES:\n"
        "Customer: 'Fifty thousand' → {\"monthly_income_inr\": 50000}, intent: provide_value\n"
        "Customer: '50,000 rupees' → {\"monthly_income_inr\": 50000}, intent: provide_value\n"
        "Customer: 'Rs. 3000' → {\"monthly_income_inr\": 3000}, intent: provide_value\n"
        "Customer: '45k per month' → {\"monthly_income_inr\": 45000}, intent: provide_value\n"
        "Customer: 'Around thirty thousand' → {\"monthly_income_inr\": 30000}, intent: provide_value\n"
        "Customer: 'I make 25 thousand' → {\"monthly_income_inr\": 25000}, intent: provide_value\n"
        "Customer: 'Thank you' → {}, intent: unclear\n\n"
        "CRITICAL: If you see ANY number in the response, extract it as monthly_income_inr. Be aggressive - any number = income."
    ),
    "qualify_followup": _node_text("qualify", "follow_up"),
    "consent": (
        "Extract: consent_given (bool).\n\n"
        "EXAMPLES:\n"
        "Customer: 'Yes' → {\"consent_given\": true}, intent: affirm\n"
        "Customer: 'Sure, go ahead' → {\"consent_given\": true}, intent: affirm\n"
        "Customer: 'Okay' → {\"consent_given\": true}, intent: affirm\n"
        "Customer: 'No' → {\"consent_given\": false}, intent: deny\n"
        "Customer: 'I don't want to' → {\"consent_given\": false}, intent: deny\n\n"
        "RULES: Any positive response = true. Any negative response = false."
    ),
    "next_step": "No slots to extract. Intent: affirm.",
    "close": "No slots to extract. Intent: unclear.",
}

# ── System prompt builder ─────────────────────────────────────────────────────

_SYSTEM_TEMPLATE = """\
You are {agent_name} from {lender_name}, conducting a commercial vehicle outbound call.
Customer name: {customer_name}

Your script for this turn (node: {node_name}):
{script_text}

{slot_guidance}

Respond ONLY with valid JSON matching this exact schema — no markdown, no preamble:
{{
  "classified_intent": "affirm" | "deny" | "provide_value" | "unclear",
  "slots_extracted": {{ <slot_key>: <value> }},
  "agent_turn_text": "<your response, strictly follow the script, max 30 words>"
}}"""


def build_messages(
    agent_name: str,
    lender_name: str,
    customer_name: str,
    node_name: str,
    asr_text: str,
) -> list[dict[str, str]]:
    """Return the messages list to pass to the LLM for a single dialog turn."""
    system = _SYSTEM_TEMPLATE.format(
        agent_name=agent_name,
        lender_name=lender_name,
        customer_name=customer_name,
        node_name=node_name,
        script_text=_NODE_SCRIPTS[node_name],
        slot_guidance=_SLOT_GUIDANCE[node_name],
    )
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    if asr_text:
        messages.append({"role": "user", "content": asr_text})
    return messages


def get_fallback_text(node_name: str, agent_name: str, lender_name: str, customer_name: str) -> str:
    """Return the raw YAML script text as a fallback when the LLM call fails."""
    template = _NODE_SCRIPTS[node_name]
    return template.format(
        agent_name=agent_name,
        lender_name=lender_name,
        customer_name=customer_name,
    )
