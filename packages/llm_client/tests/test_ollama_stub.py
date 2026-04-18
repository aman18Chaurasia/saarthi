import pytest


def test_ollama_provider_raises_not_implemented_on_init() -> None:
    from llm_client.ollama_provider import OllamaProvider

    with pytest.raises(NotImplementedError, match="NVIDIA GPU"):
        OllamaProvider()
