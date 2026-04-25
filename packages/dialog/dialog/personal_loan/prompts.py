"""Prompt assembly for the personal loan dialog nodes.

Loads personal_loan.yaml once at module import and builds per-node system prompts.
The YAML is the single source of truth for all agent script text (ADR 0002 §5).

YAML search order:
  1. PERSONAL_LOAN_YAML env var (absolute path)
  2. packages/scripts/products/personal_loan.yaml relative to repo root
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
    env_path = os.environ.get("PERSONAL_LOAN_YAML")
    if env_path:
        return yaml.safe_load(Path(env_path).read_text(encoding="utf-8"))

    # packages/dialog/dialog/personal_loan/prompts.py
    # parents[3] = packages/dialog → parents[3].parent = packages
    repo_packages = Path(__file__).parents[3]
    default_path = repo_packages / "scripts" / "products" / "personal_loan.yaml"
    if default_path.exists():
        return yaml.safe_load(default_path.read_text(encoding="utf-8"))

    raise FileNotFoundError(
        f"personal_loan.yaml not found. Set PERSONAL_LOAN_YAML env var or "
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

# Retry variants - different phrasings for each attempt
_RETRY_VARIANTS: dict[str, list[str]] = {
    "identity_confirm": [
        "Thank you. Main aapko ek personal loan offer ke baare mein baat karna chahta tha — kya abhi aapke paas 2 minute hain?",
        "Ji, main {lender_name} se bol raha hoon. Kya aap abhi baat kar sakte hain? Sirf 2 minute lagenge.",
        "Personal loan offer hai aapke liye. Abhi thoda time hai aapke paas?",
    ],
    "qualify": [
        "Great. Aapki monthly income approximately kitni hai?",
        "Samjha. Boliye, aap mahine mein roughly kitna kamate hain?",
        "Income ki baat karein - per month kitna hota hai aapka?",
    ],
    "qualify_followup": [
        "Aur aap is loan ka use kisliye karna chahte hain — home renovation, travel, ya kuch aur?",
        "Yeh loan aap kis purpose ke liye chahte hain? Jaise ghar ki repair, travel, medical?",
        "Batayiye, loan ki zaroorat kis cheez ke liye hai?",
    ],
    "consent": [
        "Main aapko ek tailored offer bhejne ke liye aapki basic details record karna chahta hoon. Kya aap consent dete hain?",
        "Aapki details record karne ki permission mil sakti hai? Phir main aapko best offer bhej sakta hoon.",
        "Kya main aapki information save kar sakta hoon offer bhejne ke liye?",
    ],
}

_SLOT_GUIDANCE: dict[str, str] = {
    "opener": "No slots to extract. classified_intent should be 'unclear'.",
    "identity_confirm": (
        "Extract: name_confirmed (bool), has_time (bool).\n\n"
        "EXAMPLES:\n"
        "Customer: 'Yes, I have 2 minutes' → {\"name_confirmed\": true, \"has_time\": true}, intent: affirm\n"
        "Customer: 'I'm looking for a loan' → {\"name_confirmed\": true, \"has_time\": true}, intent: affirm\n"
        "Customer: 'Yes this is Rahul speaking' → {\"name_confirmed\": true, \"has_time\": true}, intent: affirm\n"
        "Customer: 'I'm looking for housing loan' → {\"name_confirmed\": true, \"has_time\": true}, intent: affirm (acknowledge different product interest but continue)\n"
        "Customer: 'I'm busy right now' → {\"has_time\": false}, intent: deny\n"
        "Customer: 'What?' → {}, intent: unclear\n\n"
        "RULES:\n"
        "- has_time=true if customer engages positively OR expresses ANY loan interest (even if different product)\n"
        "- has_time=false ONLY if explicitly busy/not interested\n"
        "- If they mention a different product, acknowledge it: 'I understand you're interested in [product]. Let me also share our personal loan offer which might be helpful.'"
    ),
    "qualify": (
        "Extract: monthly_income_inr (integer).\n\n"
        "EXAMPLES:\n"
        "Customer: 'Fifty thousand' → {\"monthly_income_inr\": 50000}, intent: provide_value\n"
        "Customer: '50,000 rupees' → {\"monthly_income_inr\": 50000}, intent: provide_value\n"
        "Customer: '50,000 मेरे monthly income 50,000 है' → {\"monthly_income_inr\": 50000}, intent: provide_value\n"
        "Customer: '50,000 50,000' → {\"monthly_income_inr\": 50000}, intent: provide_value\n"
        "Customer: 'Rs. 3000' → {\"monthly_income_inr\": 3000}, intent: provide_value\n"
        "Customer: '45k per month' → {\"monthly_income_inr\": 45000}, intent: provide_value\n"
        "Customer: 'Around thirty thousand' → {\"monthly_income_inr\": 30000}, intent: provide_value\n"
        "Customer: 'I make 25 thousand' → {\"monthly_income_inr\": 25000}, intent: provide_value\n"
        "Customer: 'पचास हज़ार' → {\"monthly_income_inr\": 50000}, intent: provide_value\n"
        "Customer: 'Thank you' → {}, intent: unclear\n\n"
        "CRITICAL RULES:\n"
        "1. If you see ANY number (digits or words), extract it as monthly_income_inr\n"
        "2. Ignore surrounding Hindi/Urdu/English text - JUST find the number\n"
        "3. If number appears multiple times, use the first one\n"
        "4. Numbers like '50,000', '50000', '50k' are all the same\n"
        "5. BE AGGRESSIVE - when in doubt, extract the number!"
    ),
    "qualify_followup": (
        "Extract: loan_purpose (string).\n\n"
        "EXAMPLES:\n"
        "Customer: 'Home renovation' → {\"loan_purpose\": \"home_renovation\"}, intent: provide_value\n"
        "Customer: 'For my house repairs' → {\"loan_purpose\": \"home_renovation\"}, intent: provide_value\n"
        "Customer: 'Travel' → {\"loan_purpose\": \"travel\"}, intent: provide_value\n"
        "Customer: 'Medical emergency' → {\"loan_purpose\": \"medical\"}, intent: provide_value\n"
        "Customer: 'Education' → {\"loan_purpose\": \"education\"}, intent: provide_value\n"
        "Customer: 'Business' → {\"loan_purpose\": \"business\"}, intent: provide_value\n"
        "Customer: 'Personal use' → {\"loan_purpose\": \"other\"}, intent: provide_value\n"
        "Customer: 'मैं ये personal loan के लिए करना चाहिए' → {\"loan_purpose\": \"other\"}, intent: provide_value\n"
        "Customer: 'मेरा future secure होता है' → {\"loan_purpose\": \"other\"}, intent: provide_value\n"
        "Customer: 'financial security' → {\"loan_purpose\": \"other\"}, intent: provide_value\n"
        "Customer: 'जी हाँ' (yes) → {}, intent: affirm (NO PURPOSE - don't guess!)\n"
        "Customer: 'Thank you' → {}, intent: unclear\n\n"
        "VALID VALUES: home_renovation, travel, medical, education, business, other.\n"
        "CRITICAL RULES:\n"
        "1. If customer mentions ANY purpose/reason, extract it\n"
        "2. If customer just says 'yes' or 'ok' without mentioning purpose, SKIP this - don't guess\n"
        "3. 'personal loan' or 'loan' alone = \"other\" (generic personal use)\n"
        "4. Be flexible with mixed Hindi/English/Urdu"
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
You are {agent_name} from {lender_name}, conducting a personal loan outbound call.
Customer name: {customer_name}
Current conversation stage: {node_name}

SCRIPT GUIDANCE (adapt naturally, don't repeat verbatim):
{script_text}

{slot_guidance}

CONVERSATION RULES:
1. Listen carefully to what the customer actually says - BE RESPONSIVE, NOT SCRIPTED
2. If customer gives a number (ANY number), extract it as the slot value
3. If customer asks a question, ANSWER IT FIRST before continuing the script
4. Acknowledge their responses naturally - use phrases like "Bilkul", "Samajh gaya", "Accha", "Great"
5. If they mention a different product, acknowledge: "Main samajhta hoon, lekin personal loan bhi helpful ho sakta hai..."
6. Build rapport - use their name occasionally, sound friendly and helpful
7. Keep responses conversational in Hinglish - max 40 words (can be slightly longer if answering questions)
8. Don't ask the same question twice - if unclear, rephrase differently
9. MIXED LANGUAGE IS NORMAL - customer may use Hindi, Urdu, English, Tamil, Telugu mixed - extract information anyway
10. Add natural fillers: "Dekhiye", "Acha suniye", "Haan ji", "Ek minute" to sound human
11. If customer sounds frustrated, be empathetic: "Main samajhta hoon, tension mat lijiye"
12. Adapt your language to match customer's style (more Hindi if they use more Hindi, more English if they prefer English)

COMMON QUESTIONS & ANSWERS:
Q: Interest rate kya hai? → "Interest rate 10.5% se shuru hota hai, aapki income ke basis pe adjust hoga"
Q: EMI kitni hogi? → "Rs 50,000 loan pe approximately Rs 2,200 monthly EMI, 2 saal ke liye"
Q: Documents kya chahiye? → "Bas PAN card, Aadhaar, aur 3 mahine ki salary slip. Bahut simple process hai"
Q: Kitne din mein milega? → "Approval agar ho gaya toh 2-3 din mein amount aapke account mein aa jayega"
Q: Processing fee? → "Minimal processing fee hai, loan amount pe depend karta hai. Details SMS mein aayegi"

Respond ONLY with valid JSON matching this exact schema — no markdown, no preamble:
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
    """Return the messages list to pass to the LLM for a single dialog turn.

    Args:
        agent_name: Name of the agent
        lender_name: Name of the lending institution
        customer_name: Name of the customer
        node_name: Current dialog node
        asr_text: Latest customer utterance
        history: List of TurnRecord objects from previous turns (optional)
        retry_count: Number of retries (for dynamic rephrasing)
        sentiment_guidance: Sentiment-aware guidance to add
        memory_context: Relevant context from long-term memory
        rag_context: Relevant context from knowledge base (product info, benefits, etc.)
    """
    # Get appropriate script text (retry variant if retrying)
    script_text = get_script_text(node_name, retry_count)

    # Build system prompt
    system_parts = []

    # Add sentiment guidance if present
    if sentiment_guidance:
        system_parts.append(sentiment_guidance)

    # Add RAG context if present (knowledge base info takes priority for accuracy)
    if rag_context:
        system_parts.append(f"KNOWLEDGE BASE CONTEXT (Use this for accurate product information):\n{rag_context}")

    # Add memory context if present
    if memory_context:
        system_parts.append(memory_context)

    # Add main system prompt
    main_system = _SYSTEM_TEMPLATE.format(
        agent_name=agent_name,
        lender_name=lender_name,
        customer_name=customer_name,
        node_name=node_name,
        script_text=script_text,
        slot_guidance=_SLOT_GUIDANCE[node_name],
    )
    system_parts.append(main_system)

    # Add retry guidance if retrying
    if retry_count > 0:
        system_parts.append(f"\nNOTE: This is retry attempt {retry_count + 1}. Customer may not have understood. Rephrase more clearly.")

    # Combine all system parts
    system = "\n\n".join(system_parts)
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]

    # Add conversation history (last 4 turns for context)
    if history:
        recent_history = history[-4:] if len(history) > 4 else history
        for turn in recent_history:
            role = "assistant" if turn.speaker == "agent" else "user"
            text = turn.text if hasattr(turn, 'text') else str(turn.get('text', ''))
            if text:
                messages.append({"role": role, "content": text})

    # Add current customer utterance
    if asr_text:
        messages.append({"role": "user", "content": asr_text})

    return messages


def get_script_text(node_name: str, retry_count: int = 0) -> str:
    """Get script text for node, using retry variant if available.

    Args:
        node_name: Current dialog node
        retry_count: Number of retries (0 = first attempt)

    Returns:
        Script text (from retry variants if retry_count > 0, else from YAML)
    """
    # Use retry variant if available and we're retrying
    if retry_count > 0 and node_name in _RETRY_VARIANTS:
        variants = _RETRY_VARIANTS[node_name]
        # Cycle through variants (wrap around if needed)
        variant_index = min(retry_count - 1, len(variants) - 1)
        return variants[variant_index]

    # Default: use YAML script
    return _NODE_SCRIPTS[node_name]


def get_fallback_text(node_name: str, agent_name: str, lender_name: str, customer_name: str) -> str:
    """Return the raw YAML script text as a fallback when the LLM call fails."""
    template = _NODE_SCRIPTS[node_name]
    return template.format(
        agent_name=agent_name,
        lender_name=lender_name,
        customer_name=customer_name,
    )
