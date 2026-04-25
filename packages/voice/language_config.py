"""Multi-language support configuration for SAARTHI.

Supports 10+ Indian languages with appropriate greetings and common phrases.
"""
from __future__ import annotations

from typing import TypedDict


class LanguageConfig(TypedDict):
    """Language configuration for voice agent."""
    code: str
    name: str
    greeting: str
    closing: str
    affirmative: list[str]
    negative: list[str]
    unclear: list[str]


# Language configurations for Indian languages
LANGUAGES: dict[str, LanguageConfig] = {
    "hi-IN": {
        "code": "hi-IN",
        "name": "Hindi",
        "greeting": "Namaste",
        "closing": "Dhanyavaad",
        "affirmative": ["haan", "ji", "bilkul", "theek hai", "okay"],
        "negative": ["nahi", "na", "nahin", "mat karo"],
        "unclear": ["kya", "samajh nahi aaya", "phir se bolo"],
    },
    "en-IN": {
        "code": "en-IN",
        "name": "English",
        "greeting": "Hello",
        "closing": "Thank you",
        "affirmative": ["yes", "yeah", "sure", "okay", "alright"],
        "negative": ["no", "nope", "not interested"],
        "unclear": ["what", "pardon", "sorry"],
    },
    "ta-IN": {
        "code": "ta-IN",
        "name": "Tamil",
        "greeting": "Vanakkam",
        "closing": "Nandri",
        "affirmative": ["aam", "sari", "ok"],
        "negative": ["illai", "venda"],
        "unclear": ["enna", "puriyala"],
    },
    "te-IN": {
        "code": "te-IN",
        "name": "Telugu",
        "greeting": "Namaskaram",
        "closing": "Dhanyavadalu",
        "affirmative": ["avunu", "sare", "ok"],
        "negative": ["kadu", "vaddhu"],
        "unclear": ["enti", "artham kaledhu"],
    },
    "mr-IN": {
        "code": "mr-IN",
        "name": "Marathi",
        "greeting": "Namaskar",
        "closing": "Dhanyavad",
        "affirmative": ["hoy", "theek ahe", "chalel"],
        "negative": ["nahi", "nako"],
        "unclear": ["kay", "samajla nahi"],
    },
    "bn-IN": {
        "code": "bn-IN",
        "name": "Bengali",
        "greeting": "Nomoshkar",
        "closing": "Dhonnobad",
        "affirmative": ["hyan", "thik ache", "okay"],
        "negative": ["na", "noy"],
        "unclear": ["ki", "bujhini"],
    },
    "gu-IN": {
        "code": "gu-IN",
        "name": "Gujarati",
        "greeting": "Namaste",
        "closing": "Aabhar",
        "affirmative": ["haa", "theek chhe", "okay"],
        "negative": ["nahi", "na"],
        "unclear": ["shu", "samjhayu nahi"],
    },
    "kn-IN": {
        "code": "kn-IN",
        "name": "Kannada",
        "greeting": "Namaskara",
        "closing": "Dhanyavadagalu",
        "affirmative": ["haudu", "sari", "okay"],
        "negative": ["illa", "beda"],
        "unclear": ["enu", "artha aagilla"],
    },
    "ml-IN": {
        "code": "ml-IN",
        "name": "Malayalam",
        "greeting": "Namaskaram",
        "closing": "Nanni",
        "affirmative": ["athe", "sheriyaanu", "okay"],
        "negative": ["alla", "venda"],
        "unclear": ["enthu", "manasilaayilla"],
    },
    "pa-IN": {
        "code": "pa-IN",
        "name": "Punjabi",
        "greeting": "Sat Sri Akaal",
        "closing": "Dhannvaad",
        "affirmative": ["haan", "theek hai", "okay"],
        "negative": ["nahi", "na"],
        "unclear": ["ki", "samajh nahi aayi"],
    },
}


def get_language_config(language_code: str) -> LanguageConfig:
    """Get language configuration by code.

    Args:
        language_code: Language code (e.g., 'hi-IN', 'en-IN')

    Returns:
        LanguageConfig for the specified language

    Raises:
        KeyError: If language code is not supported
    """
    return LANGUAGES[language_code]


def get_supported_languages() -> list[str]:
    """Get list of supported language codes."""
    return list(LANGUAGES.keys())


def is_language_supported(language_code: str) -> bool:
    """Check if a language code is supported."""
    return language_code in LANGUAGES


def adapt_script_for_language(script_text: str, language_code: str) -> str:
    """Adapt a script for a specific language.

    For now, this is a simple replacement of greetings/closings.
    In production, this would use proper translation APIs.

    Args:
        script_text: Original script text in Hinglish
        language_code: Target language code

    Returns:
        Adapted script text
    """
    if language_code == "hi-IN" or language_code == "en-IN":
        # Hinglish and English use original scripts
        return script_text

    config = get_language_config(language_code)

    # Simple greeting/closing replacement
    # TODO: Integrate with proper translation API for full script translation
    adapted = script_text.replace("Namaste", config["greeting"])
    adapted = adapted.replace("Thank you", config["closing"])

    return adapted
