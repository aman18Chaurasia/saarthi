"""Tests for Hinglish code-switching."""
from guardrail.hinglish import detect_language, localize_template, should_code_switch


def test_detect_english():
    assert detect_language("Hello, how can I help you?") == "en"


def test_detect_hinglish():
    assert detect_language("Namaste! Aap ka monthly income kya hai?") == "hi-en"
    assert detect_language("My income is 25000 rupees per month") == "hi-en"


def test_detect_hindi_devanagari():
    assert detect_language("नमस्ते! मैं आपकी कैसे मदद कर सकता हूं?") == "hi"


def test_should_code_switch():
    # Customer speaks Hinglish, agent in English → switch
    assert should_code_switch("hi-en", "en") is True

    # Customer speaks English, agent in Hinglish → switch
    assert should_code_switch("en", "hi-en") is True

    # Both same → no switch
    assert should_code_switch("hi-en", "hi-en") is False


def test_localize_template():
    result = localize_template("greeting", "hi-en")
    assert "Namaste" in result

    result = localize_template("not_qualified", "hi-en", min_income=15000)
    assert "15000" in result
