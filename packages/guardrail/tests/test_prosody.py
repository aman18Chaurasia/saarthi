"""Tests for sentiment-adaptive prosody."""
from guardrail.prosody import detect_sentiment, enhance_tts_input


def test_detect_positive_sentiment():
    assert detect_sentiment("Badhai ho! Aap qualified hain.") == "positive"
    assert detect_sentiment("Congratulations, you qualify!") == "positive"


def test_detect_empathetic_sentiment():
    assert detect_sentiment("Maaf kijiye, aap qualify nahi karte.") == "empathetic"
    assert detect_sentiment("Unfortunately, you don't qualify.") == "empathetic"


def test_detect_urgent_sentiment():
    assert detect_sentiment("Please respond quickly.") == "urgent"
    assert detect_sentiment("Jaldi batayein.") == "urgent"


def test_detect_neutral_sentiment():
    assert detect_sentiment("What is your monthly income?") == "neutral"


def test_enhance_tts_input_positive():
    text, settings = enhance_tts_input("Congratulations! You qualify.")
    assert "prosody" in text  # SSML tags added
    assert settings["stability"] == 0.5  # Expressive


def test_enhance_tts_input_empathetic():
    text, settings = enhance_tts_input("Sorry, you don't qualify.")
    assert "prosody" in text
    assert settings["stability"] == 0.8  # Calm, consistent
