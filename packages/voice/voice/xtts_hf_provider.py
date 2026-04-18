import os

import httpx

from .base import BaseTTSProvider


class XTTSHfSpaceProvider(BaseTTSProvider):
    """Calls a self-hosted or shared Coqui XTTS-v2 Hugging Face Space endpoint.

    The Space must accept POST /synthesize with JSON {"text": str} and return
    raw audio bytes (wav). Set HF_SPACE_XTTS_URL in .env to your Space URL.
    """

    def __init__(self) -> None:
        self._url = os.environ["HF_SPACE_XTTS_URL"].rstrip("/") + "/synthesize"

    async def synthesize(self, text: str) -> bytes:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self._url, json={"text": text})
            resp.raise_for_status()
            return resp.content
