import pytest


def test_groq_provider_returned_when_provider_is_groq(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-key-not-real")
    from llm_client.factory import get_chat_provider
    from llm_client.groq_provider import GroqProvider

    assert isinstance(get_chat_provider(), GroqProvider)


def test_unknown_provider_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "banana")
    from llm_client.factory import get_chat_provider

    with pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
        get_chat_provider()


def test_jina_embed_provider_returned_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EMBED_PROVIDER", "jina")
    monkeypatch.setenv("JINA_API_KEY", "test-key-not-real")
    from llm_client.factory import get_embed_provider
    from llm_client.jina_provider import JinaEmbedProvider

    assert isinstance(get_embed_provider(), JinaEmbedProvider)
