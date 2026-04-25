from __future__ import annotations

import pytest

from voice.azure_provider import AzureSTTProvider


def test_azure_stt_provider_uses_stt_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AZURE_SPEECH_KEY", "test-key")
    monkeypatch.setenv("AZURE_SPEECH_REGION", "centralindia")

    provider = AzureSTTProvider()

    assert provider._base_url == "https://centralindia.stt.speech.microsoft.com"


def test_azure_stt_provider_honors_constructor_overrides() -> None:
    provider = AzureSTTProvider(api_key="override-key", region="westus")

    assert provider._base_url == "https://westus.stt.speech.microsoft.com"
    assert provider._api_key == "override-key"
