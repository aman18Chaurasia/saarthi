import os

import httpx

from .base import BaseEmbedProvider


class JinaEmbedProvider(BaseEmbedProvider):
    _URL = "https://api.jina.ai/v1/embeddings"

    def __init__(self) -> None:
        self._api_key = os.environ["JINA_API_KEY"]
        self._model = os.environ.get("JINA_EMBED_MODEL", "jina-embeddings-v3")

    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self._URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"input": [text], "model": self._model},
            )
            resp.raise_for_status()
            data: list[dict[str, object]] = resp.json()["data"]
            embedding = data[0]["embedding"]
            assert isinstance(embedding, list)
            return embedding  # type: ignore[return-value]
