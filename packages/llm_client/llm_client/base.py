from abc import ABC, abstractmethod


class BaseChatProvider(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict[str, str]]) -> str: ...


class BaseEmbedProvider(ABC):
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]: ...
