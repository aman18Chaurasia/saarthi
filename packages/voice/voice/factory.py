import os

from .base import BaseTTSProvider


def get_tts_provider() -> BaseTTSProvider:
    provider = os.environ.get("TTS_PROVIDER", "elevenlabs").lower()
    if provider == "elevenlabs":
        from .elevenlabs_provider import ElevenLabsProvider

        return ElevenLabsProvider()
    if provider == "hf_space":
        from .xtts_hf_provider import XTTSHfSpaceProvider

        return XTTSHfSpaceProvider()
    if provider == "azure":
        from .azure_provider import AzureTTSProvider

        return AzureTTSProvider()
    if provider == "mock":
        from .mock_tts_provider import MockTTSProvider

        return MockTTSProvider()
    raise ValueError(
        f"Unknown TTS_PROVIDER={provider!r}. Valid values: elevenlabs, hf_space, azure, mock"
    )
