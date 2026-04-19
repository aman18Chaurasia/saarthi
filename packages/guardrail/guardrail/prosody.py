"""Sentiment-adaptive prosody for TTS (ElevenLabs emotion tags)."""
from __future__ import annotations

from typing import Any, Literal


SentimentLabel = Literal["positive", "neutral", "negative", "empathetic", "urgent"]


def detect_sentiment(text: str, context: dict[str, Any] | None = None) -> SentimentLabel:
    """Detect sentiment from text and conversation context.

    In production, this could use:
    - LLM-based classification
    - Dedicated sentiment model (RoBERTa fine-tuned)
    - Rule-based keyword matching (MVP)
    """
    text_lower = text.lower()

    # Positive sentiment markers
    positive_markers = ["badhai", "congratulations", "qualified", "great", "perfect"]
    if any(marker in text_lower for marker in positive_markers):
        return "positive"

    # Negative/rejection markers
    negative_markers = ["maaf", "sorry", "unfortunately", "not qualified", "nahi"]
    if any(marker in text_lower for marker in negative_markers):
        return "empathetic"

    # Urgent markers (time-sensitive)
    urgent_markers = ["quickly", "jaldi", "urgent", "immediately"]
    if any(marker in text_lower for marker in urgent_markers):
        return "urgent"

    return "neutral"


def add_prosody_tags(text: str, sentiment: SentimentLabel) -> str:
    """Add ElevenLabs SSML-style emotion tags based on sentiment.

    ElevenLabs supports:
    - <break time="500ms"/> - pauses
    - <emphasis level="strong">text</emphasis> - emphasis
    - <prosody rate="fast">text</prosody> - speed
    - Custom voice stability/similarity settings
    """
    if sentiment == "positive":
        # Warm, enthusiastic tone
        return f'<prosody rate="medium" pitch="+5%">{text}</prosody>'

    elif sentiment == "empathetic":
        # Slower, softer tone for rejection
        return f'<prosody rate="slow" pitch="-5%">{text}<break time="300ms"/></prosody>'

    elif sentiment == "urgent":
        # Faster pace for time-sensitive info
        return f'<prosody rate="fast">{text}</prosody>'

    else:  # neutral
        return text


def adapt_voice_settings(sentiment: SentimentLabel) -> dict[str, float]:
    """Return ElevenLabs voice settings based on sentiment.

    Returns:
        dict with stability and similarity_boost parameters
    """
    settings = {
        "positive": {"stability": 0.5, "similarity_boost": 0.75},  # Expressive
        "empathetic": {"stability": 0.8, "similarity_boost": 0.5},  # Calm, consistent
        "urgent": {"stability": 0.3, "similarity_boost": 0.9},     # Dynamic
        "neutral": {"stability": 0.5, "similarity_boost": 0.75},   # Balanced
        "negative": {"stability": 0.7, "similarity_boost": 0.6},   # Measured
    }

    return settings.get(sentiment, settings["neutral"])


def enhance_tts_input(
    text: str,
    context: dict[str, Any] | None = None,
) -> tuple[str, dict[str, float]]:
    """Enhance text for TTS with prosody tags and voice settings.

    Returns:
        (enhanced_text, voice_settings)
    """
    sentiment = detect_sentiment(text, context)
    enhanced_text = add_prosody_tags(text, sentiment)
    voice_settings = adapt_voice_settings(sentiment)

    return enhanced_text, voice_settings
