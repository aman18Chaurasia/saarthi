"""Hinglish code-switching detection and natural transitions."""
from __future__ import annotations

import re
from typing import Literal


LanguageCode = Literal["hi", "en", "hi-en"]  # Hindi, English, Hinglish


def detect_language(text: str) -> LanguageCode:
    """Detect if text is Hindi, English, or Hinglish (code-switched).

    Heuristics:
    - Devanagari script → Hindi
    - Only Latin + common Hinglish words → Hinglish
    - Only Latin, no Hinglish markers → English
    """
    # Check for Devanagari characters
    has_devanagari = bool(re.search(r'[\u0900-\u097F]', text))

    if has_devanagari:
        return "hi"

    # Common Hinglish words (Romanized Hindi)
    hinglish_markers = [
        "aap", "mera", "kya", "hai", "nahi", "ji", "haan", "acha", "thik",
        "loan", "income", "monthly", "rupees", "thousand", "lakh", "crore",
        "emi", "tenure", "interest", "rate", "apply"
    ]

    text_lower = text.lower()
    hinglish_count = sum(1 for word in hinglish_markers if word in text_lower)

    # If 2+ Hinglish markers, likely code-switched
    if hinglish_count >= 2:
        return "hi-en"

    return "en"


def should_code_switch(
    customer_language: LanguageCode,
    current_agent_language: LanguageCode,
) -> bool:
    """Determine if agent should switch language to match customer."""
    # Always match customer's language preference
    return customer_language != current_agent_language


def get_transition_phrase(
    from_lang: LanguageCode,
    to_lang: LanguageCode,
) -> str:
    """Get natural transition phrase for language switch."""
    transitions = {
        ("en", "hi-en"): "Thik hai, let me continue in Hinglish.",
        ("hi-en", "en"): "Sure, I can continue in English.",
        ("en", "hi"): "ठीक है, मैं हिंदी में बात करूंगा।",
        ("hi", "en"): "Okay, I'll switch to English.",
    }

    return transitions.get((from_lang, to_lang), "")


# Hinglish templates for common responses
HINGLISH_TEMPLATES = {
    "greeting": "Namaste! Main aapki kaise madad kar sakta hoon?",
    "confirm_time": "Kya aapke paas 2-3 minute hain?",
    "ask_income": "Aapki monthly income kitni hai?",
    "ask_purpose": "Loan kis purpose ke liye chahiye?",
    "qualified": "Badhai ho! Aap qualify karte hain. Kya aap consent dete hain?",
    "not_qualified": "Maaf kijiye, aap abhi qualify nahi karte. Minimum income {min_income} honi chahiye.",
    "thank_you": "Dhanyavaad! Hum aapse jald hi contact karenge.",
}


def localize_template(template_key: str, language: LanguageCode, **kwargs) -> str:
    """Get localized template based on detected language."""
    if language == "hi-en":
        template = HINGLISH_TEMPLATES.get(template_key, "")
        return template.format(**kwargs)

    # For pure English or Hindi, return placeholder (full i18n deferred)
    return HINGLISH_TEMPLATES.get(template_key, "").format(**kwargs)
