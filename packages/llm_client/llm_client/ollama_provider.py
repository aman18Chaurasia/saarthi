from .base import BaseChatProvider


class OllamaProvider(BaseChatProvider):
    def __init__(self) -> None:
        raise NotImplementedError(
            "OllamaProvider requires a local NVIDIA GPU with CUDA support. "
            "This project's dev machine uses Intel UHD 620 (integrated, no CUDA). "
            "Set LLM_PROVIDER=groq in .env and supply GROQ_API_KEY instead."
        )

    async def chat(self, messages: list[dict[str, str]]) -> str:  # pragma: no cover
        raise NotImplementedError
