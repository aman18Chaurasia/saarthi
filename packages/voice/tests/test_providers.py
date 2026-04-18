import pytest


def test_elevenlabs_provider_returned_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TTS_PROVIDER", "elevenlabs")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key-not-real")
    from voice.elevenlabs_provider import ElevenLabsProvider
    from voice.factory import get_tts_provider

    assert isinstance(get_tts_provider(), ElevenLabsProvider)


def test_hf_space_provider_returned_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TTS_PROVIDER", "hf_space")
    monkeypatch.setenv("HF_SPACE_XTTS_URL", "https://example.hf.space")
    from voice.factory import get_tts_provider
    from voice.xtts_hf_provider import XTTSHfSpaceProvider

    assert isinstance(get_tts_provider(), XTTSHfSpaceProvider)


def test_unknown_tts_provider_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TTS_PROVIDER", "unknown")
    from voice.factory import get_tts_provider

    with pytest.raises(ValueError, match="Unknown TTS_PROVIDER"):
        get_tts_provider()
