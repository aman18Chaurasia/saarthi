"""Sentiment and emotion analysis from voice and text.

Analyzes both audio features (prosody) and text content to detect:
- Emotional valence (positive/negative)
- Arousal level (calm/excited)
- Frustration indicators
- Engagement level
"""
from __future__ import annotations

import re
from typing import Any, Awaitable, Callable

from pydantic import BaseModel


class Sentiment(BaseModel):
    """Sentiment analysis result."""
    valence: float  # -1.0 (negative) to +1.0 (positive)
    arousal: float  # 0.0 (calm) to 1.0 (excited)
    frustration_level: float  # 0.0 (none) to 1.0 (high)
    engagement: float  # 0.0 (disengaged) to 1.0 (highly engaged)
    detected_emotion: str  # "neutral", "happy", "frustrated", "confused", "interested"


class SentimentAnalyzer:
    """Analyzes sentiment from voice and text."""

    def __init__(
        self,
        llm_fn: Callable[[list[dict[str, str]], str, str], Awaitable[Any]] | None = None,
    ):
        """Initialize analyzer.

        Args:
            llm_fn: Optional LLM function for advanced text sentiment
        """
        self.llm_fn = llm_fn

        # Keyword patterns for quick heuristic analysis
        self.frustration_keywords = [
            "expensive", "costly", "nahi", "no", "not interested",
            "busy", "later", "don't want", "stop", "enough",
            "already told", "repeat", "again", "confusing"
        ]

        self.positive_keywords = [
            "yes", "haan", "sure", "okay", "good", "great",
            "interested", "want", "need", "chahiye", "perfect",
            "thank", "shukriya", "theek"
        ]

        self.confusion_keywords = [
            "what", "kya", "samajh nahi", "confuse", "don't understand",
            "huh", "sorry", "pardon", "repeat", "again"
        ]

        self.engagement_keywords = [
            "tell me more", "how", "kaise", "details", "aur",
            "interest rate", "emi", "documents", "process",
            "eligibility", "when", "kab"
        ]

    async def analyze(
        self,
        text: str,
        audio_features: dict[str, float] | None = None,
    ) -> Sentiment:
        """Analyze sentiment from text and optional audio features.

        Args:
            text: Customer utterance text
            audio_features: Optional dict with audio analysis:
                {
                    "pitch_mean": float,  # Hz
                    "pitch_std": float,   # variation
                    "energy_mean": float, # loudness
                    "speaking_rate": float,  # words per second
                }

        Returns:
            Sentiment analysis result
        """
        # Text-based sentiment
        text_sentiment = self._analyze_text_heuristic(text)

        # Audio-based sentiment (if available)
        if audio_features:
            audio_sentiment = self._analyze_audio_features(audio_features)
            # Weighted combination: 60% text, 40% audio
            valence = 0.6 * text_sentiment["valence"] + 0.4 * audio_sentiment["valence"]
            arousal = 0.6 * text_sentiment["arousal"] + 0.4 * audio_sentiment["arousal"]
            frustration = max(text_sentiment["frustration"], audio_sentiment["frustration"])
        else:
            valence = text_sentiment["valence"]
            arousal = text_sentiment["arousal"]
            frustration = text_sentiment["frustration"]

        # Detect primary emotion
        emotion = self._classify_emotion(valence, arousal, frustration, text)

        # Engagement level
        engagement = self._calculate_engagement(text, arousal)

        return Sentiment(
            valence=valence,
            arousal=arousal,
            frustration_level=frustration,
            engagement=engagement,
            detected_emotion=emotion,
        )

    def _analyze_text_heuristic(self, text: str) -> dict[str, float]:
        """Quick heuristic text analysis."""
        text_lower = text.lower()

        # Count keyword matches
        frustration_count = sum(1 for kw in self.frustration_keywords if kw in text_lower)
        positive_count = sum(1 for kw in self.positive_keywords if kw in text_lower)
        confusion_count = sum(1 for kw in self.confusion_keywords if kw in text_lower)

        # Valence: balance of positive vs negative
        if positive_count > frustration_count:
            valence = min(0.8, 0.3 + positive_count * 0.2)
        elif frustration_count > 0:
            valence = max(-0.8, -0.3 - frustration_count * 0.2)
        else:
            valence = 0.0

        # Arousal: short bursts or long explanations suggest high arousal
        word_count = len(text.split())
        if word_count > 20:
            arousal = 0.7  # Long response = engaged/emotional
        elif word_count < 3:
            arousal = 0.3  # Very short = disengaged or calm
        else:
            arousal = 0.5

        # Frustration
        frustration = min(1.0, frustration_count * 0.3)

        return {
            "valence": valence,
            "arousal": arousal,
            "frustration": frustration,
        }

    def _analyze_audio_features(self, features: dict[str, float]) -> dict[str, float]:
        """Analyze sentiment from audio prosody."""
        # High pitch + high variation = excited/stressed
        pitch_mean = features.get("pitch_mean", 150.0)
        pitch_std = features.get("pitch_std", 20.0)
        energy_mean = features.get("energy_mean", 0.5)
        speaking_rate = features.get("speaking_rate", 3.0)

        # Arousal from pitch variation and energy
        arousal = min(1.0, (pitch_std / 50.0) * 0.5 + (energy_mean / 1.0) * 0.5)

        # Frustration from high pitch + fast speaking
        frustration = 0.0
        if pitch_mean > 200 and speaking_rate > 4.0:
            frustration = 0.7
        elif pitch_mean > 180:
            frustration = 0.4

        # Valence (harder from audio alone, use neutral default)
        valence = 0.0

        return {
            "valence": valence,
            "arousal": arousal,
            "frustration": frustration,
        }

    def _classify_emotion(
        self,
        valence: float,
        arousal: float,
        frustration: float,
        text: str,
    ) -> str:
        """Classify primary emotion from dimensions."""
        # Frustration overrides
        if frustration > 0.6:
            return "frustrated"

        # Confusion detection
        confusion_count = sum(1 for kw in self.confusion_keywords if kw in text.lower())
        if confusion_count >= 2:
            return "confused"

        # Quadrant-based emotion
        if valence > 0.3:
            if arousal > 0.6:
                return "excited"  # or "happy"
            else:
                return "satisfied"
        elif valence < -0.3:
            if arousal > 0.6:
                return "frustrated"
            else:
                return "disappointed"
        else:
            # Neutral zone
            if arousal > 0.6:
                return "interested"
            else:
                return "neutral"

    def _calculate_engagement(self, text: str, arousal: float) -> float:
        """Calculate engagement level."""
        text_lower = text.lower()

        # Engagement keywords
        engagement_count = sum(1 for kw in self.engagement_keywords if kw in text_lower)

        # Questions indicate engagement
        question_marks = text.count("?")

        # Combine signals
        base_engagement = arousal * 0.5
        keyword_boost = min(0.3, engagement_count * 0.1)
        question_boost = min(0.2, question_marks * 0.1)

        return min(1.0, base_engagement + keyword_boost + question_boost)

    async def get_adaptive_response_guidance(self, sentiment: Sentiment) -> str:
        """Get guidance for adapting agent response based on sentiment.

        Returns:
            String guidance to prepend to agent's system prompt
        """
        if sentiment.frustration_level > 0.7:
            return """
IMPORTANT: Customer is frustrated. Adapt your response:
- Slow down, be more careful with explanations
- Show empathy: "I understand this can be frustrating..."
- Offer clear, simple next steps
- Consider offering human handoff if frustration persists
"""

        if sentiment.detected_emotion == "confused":
            return """
IMPORTANT: Customer seems confused. Adapt your response:
- Simplify your language
- Break down complex information into steps
- Ask if they need clarification: "Kya main aur explain karun?"
"""

        if sentiment.engagement < 0.3:
            return """
IMPORTANT: Customer seems disengaged. Adapt your response:
- Be more energetic and concise
- Highlight key benefits quickly
- Ask engaging questions to re-capture attention
"""

        if sentiment.detected_emotion in ("interested", "excited"):
            return """
POSITIVE: Customer is engaged and interested!
- Build on their enthusiasm
- Provide detailed information they're seeking
- Move conversation forward efficiently
"""

        return ""  # Neutral, no special guidance

    def should_offer_human_handoff(self, sentiment: Sentiment) -> bool:
        """Determine if we should offer to transfer to human agent."""
        # High frustration + low engagement = handoff candidate
        if sentiment.frustration_level > 0.8 and sentiment.engagement < 0.4:
            return True

        # Repeated confusion
        if sentiment.detected_emotion == "confused" and sentiment.valence < -0.3:
            return True

        return False

    def get_tts_adjustments(self, sentiment: Sentiment) -> dict[str, float]:
        """Get TTS parameter adjustments based on sentiment.

        Returns:
            Dict with TTS parameter adjustments:
            {
                "rate": 0.8-1.2,  # speaking rate multiplier
                "pitch_shift": -20 to +20,  # Hz
                "energy": 0.8-1.2,  # volume multiplier
            }
        """
        adjustments = {
            "rate": 1.0,
            "pitch_shift": 0.0,
            "energy": 1.0,
        }

        # Frustrated customer: slow down, lower pitch (calming)
        if sentiment.frustration_level > 0.6:
            adjustments["rate"] = 0.85
            adjustments["pitch_shift"] = -10
            adjustments["energy"] = 0.9

        # Confused: slow down slightly
        elif sentiment.detected_emotion == "confused":
            adjustments["rate"] = 0.9
            adjustments["energy"] = 1.0

        # Disengaged: be more energetic
        elif sentiment.engagement < 0.3:
            adjustments["rate"] = 1.1
            adjustments["pitch_shift"] = 5
            adjustments["energy"] = 1.15

        # Interested/excited: match their energy
        elif sentiment.detected_emotion in ("interested", "excited"):
            adjustments["rate"] = 1.05
            adjustments["energy"] = 1.1

        return adjustments
