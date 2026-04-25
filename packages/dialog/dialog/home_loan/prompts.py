"""Prompt assembly for the home_loan dialog nodes.

Loads home_loan.yaml once at module import and builds per-node system prompts.
The YAML is the single source of truth for all agent script text (ADR 0002 §5).

YAML search order:
  1. HOME_LOAN_YAML env var (absolute path)
  2. packages/scripts/products/home_loan.yaml relative to repo root
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
    env_path = os.environ.get("HOME_LOAN_YAML")
    if env_path:
        return yaml.safe_load(Path(env_path).read_text(encoding="utf-8"))

    # packages/dialog/dialog/home_loan/prompts.py
    # parents[3] = packages/dialog → parents[3].parent = packages
    repo_packages = Path(__file__).parents[3]
    default_path = repo_packages / "scripts" / "products" / "home_loan.yaml"
    if default_path.exists():
        return yaml.safe_load(default_path.read_text(encoding="utf-8"))

    raise FileNotFoundError(
        f"home_loan.yaml not found. Set HOME_LOAN_YAML env var or "
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
    "qualify_followup": (
        "Extract: property_value_inr (integer), city (string), property_type (residential|commercial).\n\n"
        "EXAMPLES:\n"
        "Customer: 'Pune mein flat dekh raha hoon, budget 80 lakh hai' → "
        "{\"city\": \"Pune\", \"property_value_inr\": 8000000, \"property_type\": \"residential\"}, intent: provide_value\n"
        "Customer: 'Mumbai, around 1.2 crore for an apartment' → "
        "{\"city\": \"Mumbai\", \"property_value_inr\": 12000000, \"property_type\": \"residential\"}, intent: provide_value\n"
        "Customer: 'Delhi mein commercial property, around 2 crore' → "
        "{\"city\": \"Delhi\", \"property_value_inr\": 20000000, \"property_type\": \"commercial\"}, intent: provide_value\n"
        "Customer: 'Bengaluru, 95 lakh' → "
        "{\"city\": \"Bengaluru\", \"property_value_inr\": 9500000}, intent: provide_value\n"
        "Customer: 'Location Gurgaon hai, budget abhi final nahi hai' → "
        "{\"city\": \"Gurgaon\"}, intent: provide_value\n"
        "Customer: 'Approx 70 lakh ka residential flat' → "
        "{\"property_value_inr\": 7000000, \"property_type\": \"residential\"}, intent: provide_value\n\n"
        "RULES: Extract any explicit city/location and any budget/property value you hear. "
        "Convert lakh/crore values to INR integers. Use property_type only when the customer clearly says "
        "residential/home/flat/apartment or commercial/shop/office."
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
You are {agent_name} from {lender_name}, conducting a home loan outbound call.
Customer name: {customer_name}
Current conversation stage: {node_name}

SCRIPT GUIDANCE (adapt naturally, don't repeat verbatim):
{script_text}

{slot_guidance}

CONVERSATION RULES:
1. Listen carefully to what the customer actually says - BE RESPONSIVE, NOT SCRIPTED
2. If customer gives a number (ANY number), extract it as the slot value
3. If customer asks a question, ANSWER IT FIRST before continuing the script
4. Acknowledge their responses naturally - use phrases like "Bilkul", "Samajh gaya", "Accha", "Bahut accha"
5. Build rapport - use their name occasionally, sound friendly and helpful
6. Keep responses conversational in Hinglish - max 40 words
7. Don't ask the same question twice - if unclear, rephrase differently
8. MIXED LANGUAGE IS NORMAL - Hindi/Urdu/English mixed - extract information anyway
9. Add natural fillers: "Dekhiye", "Acha suniye", "Haan ji" to sound human
10. If customer sounds frustrated, be empathetic: "Main samajhta hoon, tension mat lijiye"

COMMON QUESTIONS & ANSWERS:
Q: Interest rate kya hai? -> "Home loan pe 8.5% se shuru hota hai, property aur income ke basis pe adjust hoga"
Q: EMI kitni hogi? -> "20 lakh ke loan pe approximately Rs 17,000 monthly EMI, 15 saal ke liye"
Q: Documents kya chahiye? -> "Property papers, income proof, PAN card, Aadhaar. Simple process hai"
Q: Processing fee? -> "0.5% processing fee hoti hai. Details SMS mein aayegi"
Q: Kitne din mein milega? -> "Approval 5-7 working days, disbursement property documents verify hone ke baad"

Respond ONLY with valid JSON matching this exact schema - no markdown, no preamble:
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
    """Return the messages list to pass to the LLM for a single dialog turn."""
    script_text = _NODE_SCRIPTS[node_name]

    system_parts = []
    if sentiment_guidance:
        system_parts.append(sentiment_guidance)
    if rag_context:
        system_parts.append(f"KNOWLEDGE BASE CONTEXT (Use for accurate product info):\n{rag_context}")
    if memory_context:
        system_parts.append(memory_context)

    main_system = _SYSTEM_TEMPLATE.format(
        agent_name=agent_name,
        lender_name=lender_name,
        customer_name=customer_name,
        node_name=node_name,
        script_text=script_text,
        slot_guidance=_SLOT_GUIDANCE[node_name],
    )
    system_parts.append(main_system)

    if retry_count > 0:
        system_parts.append(f"\nNOTE: Retry attempt {retry_count + 1}. Customer may not have understood. Rephrase more clearly.")

    system = "\n\n".join(system_parts)
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]

    if history:
        recent_history = history[-4:] if len(history) > 4 else history
        for turn in recent_history:
            role = "assistant" if (getattr(turn, "speaker", None) or turn.get("speaker", "")) == "agent" else "user"
            text = getattr(turn, "text", None) or turn.get("text", "")
            if text:
                messages.append({"role": role, "content": str(text)})

    if asr_text:
        messages.append({"role": "user", "content": asr_text})
    return messages


def get_fallback_text(node_name: str, agent_name: str, lender_name: str, customer_name: str) -> str:
    """Return the raw YAML script text as a fallback when the LLM call fails."""
    template = _NODE_SCRIPTS[node_name]
    try:
        return template.format(
            agent_name=agent_name,
            lender_name=lender_name,
            customer_name=customer_name,
        )
    except KeyError:
        return template
