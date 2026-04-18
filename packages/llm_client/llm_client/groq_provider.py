import os

from groq import AsyncGroq

from .base import BaseChatProvider


class GroqProvider(BaseChatProvider):
    def __init__(self) -> None:
        self._client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])
        self._model = os.environ.get("GROQ_MODEL", "llama-3.1-70b-versatile")

    async def chat(self, messages: list[dict[str, str]]) -> str:
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
        )
        content = resp.choices[0].message.content
        return content or ""
