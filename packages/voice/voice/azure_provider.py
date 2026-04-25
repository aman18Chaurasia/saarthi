"""Azure Speech Service TTS provider — streaming synthesis and STT.

Uses Azure Cognitive Services for both text-to-speech (TTS) and speech-to-text (STT).
Stream() yields PCM int16 chunks as they arrive from the API.
"""
from __future__ import annotations

import asyncio
import io
import os
import time
import wave
from collections.abc import AsyncIterator, Awaitable, Callable

import httpx

from .base import BaseTTSProvider
from .errors import TTSAPIError, TTSStreamError, TTSTimeoutError

_AZURE_TTS_BASE_URL_TEMPLATE = "https://{region}.tts.speech.microsoft.com"
_AZURE_STT_BASE_URL_TEMPLATE = "https://{region}.stt.speech.microsoft.com"
_DEFAULT_VOICE = "en-IN-NeerjaNeural"  # Default to Indian English female voice
_DEFAULT_LANGUAGE = "en-US"
_DEFAULT_OUTPUT_FORMAT = "raw-16khz-16bit-mono-pcm"
_BACKOFF_S = 0.150


def _parse_retry_after(headers: httpx.Headers) -> float:
    try:
        return float(headers.get("retry-after", ""))
    except (ValueError, TypeError):
        return _BACKOFF_S


class AzureTTSProvider(BaseTTSProvider):
    """TTS provider backed by Azure Cognitive Services Speech API.

    synthesize() — non-streaming; returns all audio bytes at once.
    stream()     — async generator; yields PCM int16 chunks as they arrive.
    """

    def __init__(self) -> None:
        self._api_key: str = os.environ["AZURE_SPEECH_KEY"]
        self._region: str = os.environ.get("AZURE_SPEECH_REGION", "eastus")
        self._voice: str = os.environ.get("AZURE_SPEECH_VOICE", _DEFAULT_VOICE)
        self._base_url = _AZURE_TTS_BASE_URL_TEMPLATE.format(region=self._region)
        # Populated by stream() when the first audio chunk arrives
        self.last_first_byte_ms: float | None = None

    async def synthesize(self, text: str) -> bytes:
        """Non-streaming synthesis — returns complete audio bytes."""
        chunks = []
        async for chunk in self.stream(text):
            chunks.append(chunk)
        return b"".join(chunks)

    async def stream(
        self,
        text: str,
        voice: str | None = None,
        language: str = _DEFAULT_LANGUAGE,
        timeout_s: float = 10.0,
        max_retries: int = 2,
    ) -> AsyncIterator[bytes]:
        """Stream PCM int16 audio from Azure Speech Service.

        Yields bytes chunks (raw PCM 16kHz mono int16) as they arrive from the API.
        The first-byte latency is recorded in ``self.last_first_byte_ms``.

        Retry policy:
          • httpx timeout                → retry up to max_retries.
          • HTTP 5xx                     → retry.
          • HTTP 429                     → sleep Retry-After, retry.
          • HTTP 4xx (≠ 429)            → raise TTSAPIError immediately.
          • Mid-stream connection drop   → raise TTSStreamError (no retry).
          • Retries exhausted           → raise TTSTimeoutError or TTSAPIError.
        """
        effective_voice = voice or self._voice
        last_exc: Exception | None = None
        prev_was_429 = False

        for attempt in range(max_retries + 1):
            if attempt > 0 and not prev_was_429:
                await asyncio.sleep(_BACKOFF_S)
            prev_was_429 = False

            try:
                req_start = time.perf_counter()
                first_byte = True

                async for chunk in self._stream_once(text, effective_voice, language, timeout_s):
                    if first_byte:
                        self.last_first_byte_ms = (time.perf_counter() - req_start) * 1000
                        first_byte = False
                    yield chunk

                return  # Successful completion

            except TTSStreamError:
                raise  # Mid-stream: never retry
            except (httpx.TimeoutException, asyncio.TimeoutError) as exc:
                last_exc = exc
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status == 429:
                    await asyncio.sleep(_parse_retry_after(exc.response.headers))
                    prev_was_429 = True
                    last_exc = exc
                elif 400 <= status < 500:
                    raise TTSAPIError(
                        f"Azure Speech API error {status}",
                        status_code=status,
                    ) from exc
                else:
                    last_exc = exc

        # All retries exhausted
        if isinstance(last_exc, (httpx.TimeoutException, asyncio.TimeoutError)):
            raise TTSTimeoutError(
                f"Azure Speech first-byte timeout after {max_retries + 1} attempt(s)"
            ) from last_exc
        raise TTSAPIError(
            f"Azure Speech failed after {max_retries + 1} attempt(s): {last_exc}",
            status_code=getattr(getattr(last_exc, "response", None), "status_code", None),
        ) from last_exc

    async def _stream_once(
        self,
        text: str,
        voice: str,
        language: str,
        timeout_s: float,
    ) -> AsyncIterator[bytes]:
        """Single streaming attempt — used by stream() retry loop.

        Raises httpx.TimeoutException / HTTPStatusError before any yield (retry-safe).
        Raises TTSStreamError if the connection drops after the first chunk.
        """
        # Request raw 16kHz mono PCM so downstream browser/Twilio playback can
        # consume the bytes directly without an MP3 decode step.
        ssml = f"""<speak version='1.0' xml:lang='{language}'>
            <voice name='{voice}'>
                {text}
            </voice>
        </speak>"""

        url = f"{self._base_url}/cognitiveservices/v1"
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_s)
        ) as client:
            async with client.stream(
                "POST",
                url,
                headers={
                    "Ocp-Apim-Subscription-Key": self._api_key,
                    "Content-Type": "application/ssml+xml",
                    "X-Microsoft-OutputFormat": _DEFAULT_OUTPUT_FORMAT,
                },
                content=ssml,
            ) as response:
                response.raise_for_status()
                first_byte_received = False
                try:
                    async for chunk in response.aiter_bytes(chunk_size=4096):
                        if chunk:
                            first_byte_received = True
                            yield chunk
                except Exception as exc:
                    if first_byte_received:
                        raise TTSStreamError(
                            f"Mid-stream connection failure: {exc}"
                        ) from exc
                    raise  # Pre-first-byte failure → let retry loop handle it


class AzureSTTProvider:
    """STT provider backed by Azure Cognitive Services Speech API.
    
    Provides speech-to-text transcription as a callable async function.
    """

    def __init__(
        self,
        api_key: str | None = None,
        region: str | None = None,
    ) -> None:
        self._api_key: str = api_key or os.environ["AZURE_SPEECH_KEY"]
        self._region: str = region or os.environ.get("AZURE_SPEECH_REGION", "eastus")
        self._base_url = _AZURE_STT_BASE_URL_TEMPLATE.format(region=self._region)

    async def transcribe(
        self,
        pcm_bytes: bytes,
        language: str = "en-IN",
        timeout_s: float = 10.0,
    ) -> str:
        """Transcribe PCM audio to text using Azure Speech Service.
        
        Args:
            pcm_bytes: Raw 16-bit PCM audio at 16kHz, mono.
            language: Language code (default "en-IN" for Indian English).
            timeout_s: API timeout in seconds.
        
        Returns:
            Transcribed text.
        """
        url = f"{self._base_url}/speech/recognition/conversation/cognitiveservices/v1"
        params = {"language": language}

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_s)
        ) as client:
            response = await client.post(
                url,
                params=params,
                headers={
                    "Ocp-Apim-Subscription-Key": self._api_key,
                    "Content-Type": "audio/wav",
                },
                content=self._pcm_to_wav(pcm_bytes),
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("RecognitionStatus") == "Success":
                return result.get("DisplayText", "")
            else:
                return ""

    @staticmethod
    def _pcm_to_wav(
        pcm_bytes: bytes,
        sample_rate: int = 16000,
        channels: int = 1,
        sample_width: int = 2,
    ) -> bytes:
        """Wrap raw PCM bytes in a WAV container."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_bytes)
        return buf.getvalue()


def make_azure_transcribe_fn(
    api_key: str | None = None,
    region: str | None = None,
    language: str = "en-IN",
) -> Callable[[bytes], Awaitable[str]]:
    """Return an async callable that POSTs PCM audio to Azure Speech Service."""
    provider = AzureSTTProvider(api_key=api_key, region=region)
    print(f"[Azure STT] endpoint={provider._base_url} language={language}")

    async def transcribe(pcm_bytes: bytes) -> str:
        return await provider.transcribe(pcm_bytes, language=language)

    return transcribe
