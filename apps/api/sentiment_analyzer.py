"""Lightweight sentiment analysis for customer speech."""
from __future__ import annotations

import logging
import re
from typing import Literal

logger = logging.getLogger(__name__)

SentimentLabel = Literal["positive", "neutral", "negative", "frustrated"]

# Keyword patterns for rule-based sentiment
_POSITIVE_KEYWORDS = (
    "yes", "good", "great", "okay", "sure", "fine", "interested", "thank",
    "haan", "theek", "achha", "sahi", "ठीक", "अच्छा", "सही", "हाँ",
)
_NEGATIVE_KEYWORDS = (
    "no", "not", "don't", "expensive", "costly", "high", "reject",
    "nahi", "nai", "mat", "mehnga", "zyada", "नहीं", "महंगा", "ज्यादा",
)
_FRUSTRATION_KEYWORDS = (
    "again", "repeat", "understand", "listen", "told you",
    "phir", "dobara", "samjho", "suno", "bataya", "फिर", "दोबारा", "समझो",
)


def analyze_sentiment(text: str, history: list[str] | None = None) -> SentimentLabel:
    """Classify customer sentiment from transcript text.

    Args:
        text: Current customer utterance
        history: Optional list of recent customer utterances for context

    Returns:
        Sentiment label: positive, neutral, negative, or frustrated
    """
    if not text:
        return "neutral"

    text_lower = text.lower()

    # Check for frustration signals (repetition, impatience)
    if history and len(history) >= 2:
        # Repeated similar questions = frustration
        if _is_repetitive(text_lower, [h.lower() for h in history[-2:]]):
            return "frustrated"

    if any(keyword in text_lower for keyword in _FRUSTRATION_KEYWORDS):
        return "frustrated"

    # Negation patterns
    has_negation = any(neg in text_lower for neg in ["no", "not", "don't", "nahi", "mat", "नहीं"])

    # Count positive/negative keywords
    positive_count = sum(1 for kw in _POSITIVE_KEYWORDS if kw in text_lower)
    negative_count = sum(1 for kw in _NEGATIVE_KEYWORDS if kw in text_lower)

    # Question marks can indicate confusion/concern
    if text.count("?") >= 2:
        negative_count += 1

    # Classify based on keyword balance
    if has_negation and negative_count > positive_count:
        return "negative"
    elif positive_count > negative_count:
        return "positive"
    elif negative_count > 0:
        return "negative"

    return "neutral"


def _is_repetitive(current: str, recent: list[str]) -> bool:
    """Check if current utterance is similar to recent ones (indicating frustration)."""
    if not recent:
        return False

    # Simple token overlap check
    current_tokens = set(current.split())
    for prev in recent:
        prev_tokens = set(prev.split())
        overlap = len(current_tokens & prev_tokens)
        if overlap >= min(3, len(current_tokens) // 2):
            return True

    return False


def get_prosody_params(sentiment: SentimentLabel) -> dict[str, float]:
    """Get TTS prosody parameters based on sentiment.

    Returns:
        Dict with 'rate' and 'pitch' multipliers (1.0 = normal)

    Examples:
        positive   → {"rate": 1.05, "pitch": 1.1}  (slightly faster, higher)
        negative   → {"rate": 0.95, "pitch": 0.95} (slower, lower)
        frustrated → {"rate": 0.9,  "pitch": 0.9}  (slower, calmer)
        neutral    → {"rate": 1.0,  "pitch": 1.0}  (normal)
    """
    prosody_map = {
        "positive": {"rate": 1.05, "pitch": 1.1},
        "negative": {"rate": 0.95, "pitch": 0.95},
        "frustrated": {"rate": 0.9, "pitch": 0.9},
        "neutral": {"rate": 1.0, "pitch": 1.0},
    }

    return prosody_map.get(sentiment, {"rate": 1.0, "pitch": 1.0})


def wrap_with_ssml(text: str, sentiment: SentimentLabel) -> str:
    """Wrap text in SSML with sentiment-adjusted prosody.

    Args:
        text: Plain text to speak
        sentiment: Detected customer sentiment

    Returns:
        SSML-formatted string with prosody tags

    Example:
        >>> wrap_with_ssml("Hello there", "positive")
        '<speak><prosody rate="1.05" pitch="+10%">Hello there</prosody></speak>'
    """
    params = get_prosody_params(sentiment)

    # Convert multipliers to percentage strings
    rate_pct = f"{(params['rate'] - 1.0) * 100:+.0f}%"
    pitch_pct = f"{(params['pitch'] - 1.0) * 100:+.0f}%"

    # Skip SSML if neutral (no adjustment)
    if sentiment == "neutral":
        return text

    return (
        f'<speak>'
        f'<prosody rate="{rate_pct}" pitch="{pitch_pct}">{text}</prosody>'
        f'</speak>'
    )
