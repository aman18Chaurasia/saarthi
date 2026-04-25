"""Prompt assembly for the msme_business dialog nodes.

Loads msme_business_loan.yaml once at module import and builds per-node system prompts.
The YAML is the single source of truth for all agent script text (ADR 0002 §5).

YAML search order:
  1. MSME_BUSINESS_YAML env var (absolute path)
  2. packages/scripts/products/msme_business_loan.yaml relative to repo root
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
    env_path = os.environ.get("MSME_BUSINESS_YAML")
    if env_path:
        return yaml.safe_load(Path(env_path).read_text(encoding="utf-8"))

    # packages/dialog/dialog/msme_business/prompts.py
    # parents[3] = packages/dialog → parents[3].parent = packages
    repo_packages = Path(__file__).parents[3]
    default_path = repo_packages / "scripts" / "products" / "msme_business_loan.yaml"
    if default_path.exists():
        return yaml.safe_load(default_path.read_text(encoding="utf-8"))

    raise FileNotFoundError(
        f"msme_business_loan.yaml not found. Set MSME_BUSINESS_YAML env var or "
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
        "Extract: monthly_revenue_inr (integer).\n\n"
        "EXAMPLES:\n"
        "Customer: 'Monthly revenue 5 lakh hai' → {\"monthly_revenue_inr\": 500000}, intent: provide_value\n"
        "Customer: 'Around 2.5 lakh per month' → {\"monthly_revenue_inr\": 250000}, intent: provide_value\n"
        "Customer: '50,000 turnover hai' → {\"monthly_revenue_inr\": 50000}, intent: provide_value\n"
        "Customer: '3 lakh ki sale hoti hai' → {\"monthly_revenue_inr\": 300000}, intent: provide_value\n"
        "Customer: 'Thank you' → {}, intent: unclear\n\n"
        "CRITICAL: If you see ANY monthly revenue, turnover, sales, or business collection number, extract it as monthly_revenue_inr."
    ),
    "qualify_followup": (
        "Extract: business_purpose (string).\n\n"
        "EXAMPLES:\n"
        "Customer: 'Working capital ke liye' → {\"business_purpose\": \"working_capital\"}, intent: provide_value\n"
        "Customer: 'Business expansion' → {\"business_purpose\": \"expansion\"}, intent: provide_value\n"
        "Customer: 'Machinery kharidni hai' → {\"business_purpose\": \"machinery\"}, intent: provide_value\n"
        "Customer: 'Inventory aur stock ke liye' → {\"business_purpose\": \"inventory\"}, intent: provide_value\n\n"
        "RULES: Map customer wording to the closest business purpose label: working_capital, expansion, machinery, inventory, or other."
    ),
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
You are {agent_name} from {lender_name}, conducting an MSME business loan outbound call.
Customer name: {customer_name}
Current conversation stage: {node_name}

SCRIPT GUIDANCE (adapt naturally):
{script_text}

{slot_guidance}

CONVERSATION RULES:
1. BE RESPONSIVE — listen to what the customer actually says
2. Extract ANY number/purpose you hear as the relevant slot value
3. Answer questions FIRST before continuing the script
4. Acknowledge naturally: "Bilkul", "Bahut accha"
5. Keep responses conversational in Hinglish — max 40 words
6. MIXED LANGUAGE is normal — extract info anyway

COMMON QUESTIONS & ANSWERS:
Q: Interest rate? -> "MSME loan pe 12-18% per annum, business vintage pe depend karta hai"
Q: Kitna loan milega? -> "Rs 1 lakh se 2 crore tak, turnover ke basis pe"
Q: Documents? -> "GST returns, bank statements, business proof chahiye"
Q: Collateral chahiye? -> "Rs 10 lakh tak unsecured, usse zyada pe collateral lag sakta hai"

Respond ONLY with valid JSON — no markdown, no preamble:
{{
  "classified_intent": "affirm" | "deny" | "provide_value" | "unclear",
  "slots_extracted": {{ <slot_key>: <value> }},
  "agent_turn_text": "<natural conversational response in Hinglish>"
}}"""


def build_messages(
    agent_name: str,
    lender_name: str,
    customer_name: str,
    node_name: str,
    asr_text: str,
    history: list[Any] | None = None,
    retry_count: int = 0,
    sentiment_guidance: str = "",
    memory_context: str = "",
    rag_context: str = "",
) -> list[dict[str, str]]:
    system_parts = []
    if sentiment_guidance:
        system_parts.append(sentiment_guidance)
    if rag_context:
        system_parts.append(f"KNOWLEDGE BASE CONTEXT:\n{rag_context}")
    if memory_context:
        system_parts.append(memory_context)
    main_system = _SYSTEM_TEMPLATE.format(
        agent_name=agent_name, lender_name=lender_name, customer_name=customer_name,
        node_name=node_name, script_text=_NODE_SCRIPTS[node_name],
        slot_guidance=_SLOT_GUIDANCE[node_name],
    )
    system_parts.append(main_system)
    if retry_count > 0:
        system_parts.append(f"\nNOTE: Retry {retry_count + 1}. Rephrase more clearly.")
    messages: list[dict[str, str]] = [{"role": "system", "content": "\n\n".join(system_parts)}]
    if history:
        for turn in (history[-4:] if len(history) > 4 else history):
            role = "assistant" if (getattr(turn, "speaker", None) or turn.get("speaker", "")) == "agent" else "user"
            text = getattr(turn, "text", None) or turn.get("text", "")
            if text:
                messages.append({"role": role, "content": str(text)})
    if asr_text:
        messages.append({"role": "user", "content": asr_text})
    return messages


def get_fallback_text(node_name: str, agent_name: str, lender_name: str, customer_name: str) -> str:
    template = _NODE_SCRIPTS[node_name]
    try:
        return template.format(agent_name=agent_name, lender_name=lender_name, customer_name=customer_name)
    except KeyError:
        return template
