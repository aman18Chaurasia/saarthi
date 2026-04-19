"""Pipecat pipeline factory for SAARTHI Phase 1 voice calls.

build_pipeline() wires:
  AudioRawFrame in
    -> VADProcessor (webrtcvad, 20 ms frames, speech boundaries)
    -> ASRProcessor (Groq Whisper, utterance buffer)
    -> LangGraphProcessor (personal-loan dialog state machine)
    -> TTSProcessor (ElevenLabs turbo_v2_5 streaming)
  AudioRawFrame out (PCM 16 kHz mono)

All external API calls are injected as callables so the pipeline is
fully unit-testable without network access.
"""
from __future__ import annotations

import io
import inspect
import os
import wave
from collections.abc import Awaitable, Callable
from typing import Any

from groq import AsyncGroq
from pipecat.pipeline.pipeline import Pipeline

# Phase 2: Dynamic imports per product (see build_pipeline)
from dialog.personal_loan.state import DialogState  # type hint only
from frame_processors.asr_processor import ASRProcessor
from frame_processors.langgraph_processor import LangGraphProcessor
from frame_processors.tts_processor import TTSProcessor
from frame_processors.vad_processor import VADProcessor

# Groq Whisper endpoint
_GROQ_WHISPER_MODEL = os.environ.get("GROQ_WHISPER_MODEL", "whisper-large-v3")


def _pcm_to_wav(
    pcm_bytes: bytes,
    sample_rate: int = 16000,
    channels: int = 1,
    sample_width: int = 2,
) -> bytes:
    """Wrap raw PCM bytes in a WAV container (required by Groq Whisper)."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()


def make_groq_transcribe_fn(
    api_key: str,
    model: str = _GROQ_WHISPER_MODEL,
) -> Callable[[bytes], Awaitable[str]]:
    """Return an async callable that POSTs PCM audio to Groq Whisper."""
    client = AsyncGroq(api_key=api_key)

    async def transcribe(pcm_bytes: bytes) -> str:
        wav_bytes = _pcm_to_wav(pcm_bytes)
        result = await client.audio.transcriptions.create(
            file=("audio.wav", wav_bytes, "audio/wav"),
            model=model,
        )
        return result.text  # type: ignore[attr-defined]

    return transcribe


def _build_product_graph(
    build_graph: Callable[..., Any],
    llm_fn: Callable[..., Awaitable[Any]],
    eligibility_fn: Callable[..., Awaitable[Any]] | None,
) -> Any:
    params = inspect.signature(build_graph).parameters
    if "eligibility_fn" in params:
        return build_graph(llm_fn, eligibility_fn=eligibility_fn)
    return build_graph(llm_fn)


def build_pipeline(
    call_id: str,
    initial_state: DialogState,
    *,
    # Injectable dependencies; callers can substitute mocks in tests
    transcribe_fn: Callable[[bytes], Awaitable[str]] | None = None,
    llm_fn: Callable[..., Awaitable[Any]] | None = None,
    tts_provider: object | None = None,
    vad_impl: object | None = None,
) -> tuple[Pipeline, Any, dict[str, Any]]:
    """Build a per-call Pipecat pipeline with all processors wired.

    Returns:
        (pipeline, graph_app, graph_config); the caller must have already
        invoked graph_app.invoke(initial_state.model_dump(), graph_config)
        (i.e. the opener node must run before the first customer utterance).

    Args:
        call_id:        Unique identifier for this call (used as LangGraph thread_id).
        initial_state:  Initial DialogState for the call.
        transcribe_fn:  Optional override for ASR (test mock).
        llm_fn:         Optional override for dialog LLM (test mock).
        tts_provider:   Optional override for TTS (test mock).
        vad_impl:       Optional override for webrtcvad.Vad (test mock).
    """
    # ASR
    if transcribe_fn is None:
        api_key = os.environ["GROQ_API_KEY"]
        transcribe_fn = make_groq_transcribe_fn(api_key)

    # Phase 2: Dynamically load dialog module for product
    product = initial_state.product
    dialog_module = __import__(f"dialog.{product}.graph", fromlist=["build_graph"])
    schema_module = __import__(f"dialog.{product}.schema", fromlist=["StructuredAgentResponse"])
    build_graph = dialog_module.build_graph
    StructuredAgentResponse = schema_module.StructuredAgentResponse

    # Dialog LLM (Groq JSON mode)
    if llm_fn is None:
        from llm_client.groq_provider import GroqProvider
        from llm_client.schema import StructuredAgentResponse as _SAR

        _llm_provider = GroqProvider()

        async def _groq_llm_fn(
            messages: list[dict[str, str]], node_name: str, asr_text: str
        ) -> StructuredAgentResponse:
            return await _llm_provider.json_mode(messages, _SAR)  # type: ignore[return-value]

        llm_fn = _groq_llm_fn

    # Phase 2: Eligibility function (optional, graceful fallback if Neo4j down)
    try:
        from eligibility.checker import check_eligibility
        eligibility_fn = check_eligibility
    except Exception:
        eligibility_fn = None

    # LangGraph dialog app
    app = _build_product_graph(build_graph, llm_fn, eligibility_fn)
    graph_config: dict[str, Any] = {"configurable": {"thread_id": call_id}}

    # TTS
    if tts_provider is None:
        tts_provider_name = os.environ.get("TTS_PROVIDER", "elevenlabs")
        if tts_provider_name == "mock":
            from voice.mock_tts_provider import MockTTSProvider

            tts_provider = MockTTSProvider()
        else:
            from voice.elevenlabs_provider import ElevenLabsProvider

            tts_provider = ElevenLabsProvider()

    # Processor chain
    vad = VADProcessor(vad_impl=vad_impl)
    asr = ASRProcessor(transcribe_fn=transcribe_fn, user_id=call_id)
    langgraph = LangGraphProcessor(app=app, config=graph_config)
    tts = TTSProcessor(tts_provider=tts_provider)

    pipeline = Pipeline([vad, asr, langgraph, tts])

    return pipeline, app, graph_config
