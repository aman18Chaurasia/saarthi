import os

from elevenlabs.client import AsyncElevenLabs

from .base import BaseTTSProvider


class ElevenLabsProvider(BaseTTSProvider):
    def __init__(self) -> None:
        self._client = AsyncElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
        self._voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "Rachel")

    async def synthesize(self, text: str) -> bytes:
        audio_iter = await self._client.generate(
            text=text,
            voice=self._voice_id,
            model="eleven_turbo_v2",
        )
        chunks: list[bytes] = []
        async for chunk in audio_iter:
            chunks.append(chunk)
        return b"".join(chunks)
