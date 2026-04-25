"""Pipecat pipeline factory for SAARTHI voice calls.

build_pipeline() wires:
  AudioRawFrame in
    -> VADProcessor (webrtcvad, 20 ms frames, speech boundaries)
    -> ASRProcessor (Groq Whisper, utterance buffer)
    -> LangGraphProcessor (dynamic product dialog state machine)
    -> TTSProcessor (configured streaming TTS provider)
  AudioRawFrame out (PCM 16 kHz mono)

All external API calls are injected as callables so the pipeline is
fully unit-testable without network access.

The llm_fn is wrapped by LiveConversationSupervisor for every call,
providing: shared compliance guidance, conversation memory, sentiment
analysis, objection routing, and live RAG for all 10 products.
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
from .frame_processors.asr_processor import ASRProcessor
from .frame_processors.langgraph_processor import LangGraphProcessor
from .frame_processors.tts_processor import TTSProcessor
from .frame_processors.vad_processor import VADProcessor

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
    rag_fn: Callable[..., Awaitable[Any]] | None = None,
) -> Any:
    params = inspect.signature(build_graph).parameters
    kwargs = {}
    if "eligibility_fn" in params:
        kwargs["eligibility_fn"] = eligibility_fn
    if "rag_fn" in params:
        kwargs["rag_fn"] = rag_fn
    return build_graph(llm_fn, **kwargs) if kwargs else build_graph(llm_fn)


def build_pipeline(
    call_id: str,
    initial_state: DialogState,
    *,
    language: str = "en-IN",
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
        asr_provider = os.environ.get("ASR_PROVIDER", "groq").lower()
        if asr_provider == "azure":
            from voice.azure_provider import make_azure_transcribe_fn
            transcribe_fn = make_azure_transcribe_fn(language=language)
        else:
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

    # Phase 2: RAG function (optional, knowledge base retrieval)
    try:
        from rag.retriever import retrieve_context
        rag_fn = retrieve_context
    except Exception:
        rag_fn = None

    # Wrap llm_fn with LiveConversationSupervisor for ALL products.
    # This adds: compliance guidance, conversation memory, sentiment analysis,
    # objection routing hints, and live RAG context for product questions.
    try:
        from dialog.live_supervisor import build_supervised_llm_fn
        llm_fn = build_supervised_llm_fn(
            call_id=call_id,
            product=product,
            base_llm_fn=llm_fn,
            rag_fn=rag_fn,
        )
    except Exception as _sup_err:
        import logging as _logging
        _logging.getLogger(__name__).warning(
            "LiveConversationSupervisor unavailable (%s); using base llm_fn.", _sup_err
        )

    # LangGraph dialog app
    app = _build_product_graph(build_graph, llm_fn, eligibility_fn, rag_fn)
    graph_config: dict[str, Any] = {"configurable": {"thread_id": call_id}}

    # TTS
    if tts_provider is None:
        from voice.factory import get_tts_provider

        tts_provider = get_tts_provider()

    # Processor chain
    vad = VADProcessor(vad_impl=vad_impl)
    asr = ASRProcessor(transcribe_fn=transcribe_fn, user_id=call_id)
    langgraph = LangGraphProcessor(app=app, config=graph_config)
    tts = TTSProcessor(tts_provider=tts_provider, language=language)

    pipeline = Pipeline([vad, asr, langgraph, tts])

    return pipeline, app, graph_config
