import os

from .base import BaseChatProvider, BaseEmbedProvider


def get_chat_provider() -> BaseChatProvider:
    provider = os.environ.get("LLM_PROVIDER", "groq").lower()
    if provider == "groq":
        from .groq_provider import GroqProvider

        return GroqProvider()
    if provider == "ollama":
        from .ollama_provider import OllamaProvider

        return OllamaProvider()  # raises NotImplementedError with guidance
    raise ValueError(
        f"Unknown LLM_PROVIDER={provider!r}. Valid values: groq, ollama"
    )


def get_embed_provider() -> BaseEmbedProvider:
    provider = os.environ.get("EMBED_PROVIDER", "jina").lower()
    if provider == "jina":
        from .jina_provider import JinaEmbedProvider

        return JinaEmbedProvider()
    raise ValueError(
        f"Unknown EMBED_PROVIDER={provider!r}. Valid values: jina, gemini"
    )
