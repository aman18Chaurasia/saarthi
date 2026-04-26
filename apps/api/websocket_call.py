"""FastAPI WebSocket endpoint for Phase 1 browser voice calls.

The endpoint owns the wire protocol from ADR 0002 section 3 and delegates
audio/dialog work to a per-call runtime. Tests inject a fake runtime so no Groq,
ElevenLabs, or Postgres calls are made.
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Response
from pydantic import BaseModel, ValidationError
from sqlmodel import select
from pipecat.frames.frames import (
    ErrorFrame,
    Frame,
    TTSAudioRawFrame,
    TextFrame,
    TranscriptionFrame,
)
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.frame_processor import FrameDirection
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from twilio.twiml.voice_response import VoiceResponse

from dialog.slot_requirements import determine_outcome
from dialog.personal_loan.state import DialogState
from .db import AsyncSessionLocal
from .frames import LatencyFrame
from .metrics import get_collector
from .models.call import Call
from .pipeline import build_pipeline

router = APIRouter()

_AUDIO_PREFIX = b"\x01"
_AUDIO_SAMPLE_RATE = 16000
_AUDIO_CHANNELS = 1
_E164_PHONE_RE = re.compile(r"^\+[1-9]\d{7,14}$")
_LOCAL_API_HOSTS = ("localhost", "127.0.0.1", "0.0.0.0")
_OUTBOUND_CALL_CONTEXT: dict[str, "OutboundCallPayload"] = {}
_PRODUCT_ALIASES = {
    "loan_against_property": "lap_secured",
    "commercial_vehicle_loan": "commercial_vehicle",
    "four_wheeler_loan": "four_wheeler",
    "msme_business_loan": "msme_business",
}
_VALID_PRODUCTS = {
    "personal_loan",
    "home_loan",
    "education_loan",
    "gold_loan",
    "credit_card",
    "unsecured_loan",
    "lap_secured",
    "commercial_vehicle",
    "four_wheeler",
    "msme_business",
}


class StartCallPayload(BaseModel):
    type: str
    call_id: str
    customer_id: str
    product: str
    language: str = "en-IN"
    agent_name: str
    lender_name: str
    customer_name: str


class OutboundCallPayload(BaseModel):
    customer_phone: str
    product: str
    language: str = "en-IN"
    agent_name: str
    lender_name: str
    customer_name: str


def _normalize_phone_number(phone: str) -> str:
    normalized = re.sub(r"[\s().-]+", "", phone.strip())
    if normalized.startswith("00"):
        normalized = f"+{normalized[2:]}"
    if not _E164_PHONE_RE.fullmatch(normalized):
        raise HTTPException(
            status_code=400,
            detail=(
                "customer_phone must be E.164 format, for example +919876543210. "
                "Remove spaces, leading zeroes, and local dialing prefixes."
            ),
        )
    return normalized


def _twilio_stream_url(api_base_url: str, call_id: str) -> str:
    base_url = api_base_url.strip().rstrip("/")
    if not base_url:
        raise HTTPException(status_code=500, detail="API_BASE_URL is not configured")

    public_host = base_url.replace("https://", "").replace("http://", "").split("/", 1)[0]
    if any(public_host.startswith(host) for host in _LOCAL_API_HOSTS):
        raise HTTPException(
            status_code=400,
            detail=(
                "API_BASE_URL must be your public HTTPS ngrok URL for real Twilio calls, "
                "not localhost."
            ),
        )
    if not base_url.startswith("https://"):
        raise HTTPException(
            status_code=400,
            detail="API_BASE_URL must start with https:// so Twilio can open a secure media stream.",
        )

    return f"wss://{public_host}/ws/twilio/{call_id}"


def _normalize_product(product: str) -> str:
    return _PRODUCT_ALIASES.get(product, product)


class EndCallPayload(BaseModel):
    type: str
    call_id: str
    reason: str


class CallRuntime(Protocol):
    async def start(self) -> None:
        """Start processing and enqueue any initial frames."""

    async def queue_audio(self, audio: bytes) -> None:
        """Queue one raw PCM audio chunk."""

    async def next_frame(self) -> Frame:
        """Return the next outbound Pipecat frame."""

    async def stop(self) -> None:
        """Flush and stop the runtime."""

    async def close(self) -> None:
        """Cancel and cleanup resources."""

    async def get_dialog_state(self) -> Any | None:
        """Return the latest dialog state when available."""


class PipecatCallRuntime:
    """Runtime adapter between the WebSocket endpoint and Pipecat PipelineTask."""

    def __init__(self, initial_state: DialogState, db_session: Any | None = None) -> None:
        self._initial_state = initial_state
        self._outgoing: asyncio.Queue[Frame] = asyncio.Queue()
        self._runner_task: asyncio.Task[None] | None = None
        self._task: PipelineTask | None = None
        self._graph_app: Any | None = None
        self._graph_config: dict[str, Any] | None = None
        self._language = "en-IN"
        self._db_session = db_session

    def set_language(self, language: str | None) -> None:
        if language:
            self._language = language

    async def start(self) -> None:
        pipeline, graph_app, graph_config = build_pipeline(
            self._initial_state.call_id,
            self._initial_state,
            language=self._language,
            db_session=self._db_session,
        )
        self._graph_app = graph_app
        self._graph_config = graph_config

        opener_state = await graph_app.ainvoke(self._initial_state.model_dump(), graph_config)
        opener_text = _extract_agent_text(opener_state)

        task = PipelineTask(
            pipeline,
            cancel_on_idle_timeout=False,
            enable_rtvi=False,
            enable_turn_tracking=False,
            params=PipelineParams(
                audio_in_sample_rate=_AUDIO_SAMPLE_RATE,
                audio_out_sample_rate=_AUDIO_SAMPLE_RATE,
            ),
        )
        task.set_reached_downstream_filter(
            (TranscriptionFrame, TextFrame, TTSAudioRawFrame, LatencyFrame, ErrorFrame)
        )

        @task.event_handler("on_frame_reached_downstream")
        async def on_frame_reached_downstream(_: PipelineTask, frame: Frame) -> None:
            await self._outgoing.put(frame)

        self._task = task
        self._runner_task = asyncio.create_task(PipelineRunner().run(task))

        if opener_text:
            opener_frame = TextFrame(text=opener_text)
            opener_frame.metadata["node_name"] = _state_get(opener_state, "current_node", "opener")
            opener_frame.metadata["turn_index"] = _state_get(opener_state, "turn_index", 0)
            await task.queue_frame(opener_frame)

    async def queue_audio(self, audio: bytes) -> None:
        if self._task is None:
            raise RuntimeError("Call runtime has not been started")

        from pipecat.frames.frames import UserAudioRawFrame

        await self._task.queue_frame(
            UserAudioRawFrame(
                audio=audio,
                sample_rate=_AUDIO_SAMPLE_RATE,
                num_channels=_AUDIO_CHANNELS,
                user_id=self._initial_state.call_id,
            ),
            FrameDirection.DOWNSTREAM,
        )

    async def next_frame(self) -> Frame:
        return await self._outgoing.get()

    async def stop(self) -> None:
        if self._task is None:
            return
        await self._task.stop_when_done()
        if self._runner_task is not None:
            await asyncio.wait_for(self._runner_task, timeout=5.0)

    async def close(self) -> None:
        if self._task is not None and not self._task.has_finished():
            await self._task.cancel(reason="websocket_closed")
        if self._runner_task is not None:
            try:
                await asyncio.wait_for(self._runner_task, timeout=2.0)
            except TimeoutError:
                self._runner_task.cancel()
                await asyncio.gather(self._runner_task, return_exceptions=True)

    async def get_dialog_state(self) -> Any | None:
        if self._graph_app is None or self._graph_config is None:
            return None
        snapshot = await self._graph_app.aget_state(self._graph_config)
        return snapshot.values


RuntimeFactory = Callable[[DialogState], CallRuntime]


@dataclass
class WebSocketTurnState:
    started_at: float = field(default_factory=time.perf_counter)
    sequence: int = 0
    turn_index: int = 0
    stream_sid: str | None = None
    outbound_chunk: int = 0
    transcript: list[dict[str, Any]] = field(default_factory=list)
    latency_samples: dict[str, list[float]] = field(
        default_factory=lambda: {"asr": [], "llm": [], "tts": [], "e2e": []}
    )
    error_count: int = 0
    audio_failed: bool = False
    persisted: bool = False
    latency: dict[str, float] = field(
        default_factory=lambda: {
            "asr_ms": 0.0,
            "llm_ms": 0.0,
            "tts_first_byte_ms": 0.0,
        }
    )


def _state_get(state: Any, key: str, default: Any = None) -> Any:
    if isinstance(state, dict):
        return state.get(key, default)
    if hasattr(state, "model_dump"):
        return state.model_dump().get(key, default)
    return getattr(state, key, default)


def _extract_agent_text(state: Any) -> str:
    history = _state_get(state, "history", [])
    for turn in reversed(list(history)):
        if hasattr(turn, "speaker") and turn.speaker == "agent":
            return str(turn.text)
        if isinstance(turn, dict) and turn.get("speaker") == "agent":
            return str(turn.get("text", ""))
    return ""


async def _resolve_outcome(runtime: CallRuntime | None, fallback: str = "dropped") -> str:
    if runtime is None:
        return fallback
    try:
        dialog_state = await runtime.get_dialog_state()
    except Exception:
        return fallback
    if not dialog_state:
        return fallback
    slots = _state_get(dialog_state, "slots", {})
    product = _state_get(dialog_state, "product", None)
    return determine_outcome(slots, product=product)


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = round((len(ordered) - 1) * (percentile / 100))
    return round(ordered[index], 2)


def _latency_stats(samples: dict[str, list[float]]) -> dict[str, float]:
    stats: dict[str, float] = {}
    for hop, values in samples.items():
        stats[f"{hop}_p50"] = _percentile(values, 50)
        stats[f"{hop}_p95"] = _percentile(values, 95)
    return stats


def _redact_text(text: str) -> str:
    try:
        from guardrail.redact import redact_str

        return redact_str(text)
    except Exception:
        return text


def _append_transcript(
    state: WebSocketTurnState,
    *,
    speaker: str,
    text: str,
    node: str,
    turn_index: int,
) -> None:
    if not text:
        return
    state.transcript.append(
        {
            "speaker": speaker,
            "text": _redact_text(text),
            "node": node,
            "turn_index": turn_index,
        }
    )


async def _create_call_record(payload: StartCallPayload, state: WebSocketTurnState) -> None:
    if os.environ.get("SAARTHI_DISABLE_CALL_PERSISTENCE") == "1":
        return

    try:
        async with AsyncSessionLocal() as session:
            result = await session.exec(select(Call).where(Call.call_id == payload.call_id))
            if result.first():
                return

            session.add(
                Call(
                    call_id=payload.call_id,
                    customer_id=payload.customer_id,
                    product=payload.product,
                    agent_name=payload.agent_name,
                    lender_name=payload.lender_name,
                    customer_name_redacted=_redact_text(payload.customer_name),
                    status="in_progress",
                    started_at=datetime.utcnow(),
                    turn_count=0,
                    error_count=0,
                    audio_failed=False,
                )
            )
            await session.commit()
    except Exception as exc:
        state.error_count += 1
        print(f"[Persistence] Failed to create call record {payload.call_id}: {exc}")


async def _finalize_call_record(
    payload: StartCallPayload | None,
    state: WebSocketTurnState,
    *,
    status: str,
    outcome: str,
    dialog_state: Any | None = None,
) -> None:
    if os.environ.get("SAARTHI_DISABLE_CALL_PERSISTENCE") == "1":
        return

    if payload is None or state.persisted:
        return

    try:
        async with AsyncSessionLocal() as session:
            result = await session.exec(select(Call).where(Call.call_id == payload.call_id))
            call = result.first()
            if call is None:
                call = Call(
                    call_id=payload.call_id,
                    customer_id=payload.customer_id,
                    product=payload.product,
                    agent_name=payload.agent_name,
                    lender_name=payload.lender_name,
                    customer_name_redacted=_redact_text(payload.customer_name),
                    status=status,
                )
                session.add(call)

            ended_at = datetime.utcnow()
            call.status = status
            call.outcome = outcome
            call.ended_at = ended_at
            call.duration_s = round(time.perf_counter() - state.started_at, 2)
            call.turn_count = max(state.turn_index, len(state.transcript))
            call.error_count = state.error_count
            call.audio_failed = state.audio_failed
            call.transcript_redacted = state.transcript
            call.latency_stats = _latency_stats(state.latency_samples)
            slots = _state_get(dialog_state, "slots", {})
            if hasattr(slots, "model_dump"):
                slots = slots.model_dump()
            if isinstance(slots, dict):
                try:
                    from guardrail.redact import redact_dict

                    call.slots_redacted = redact_dict(slots)
                except Exception:
                    call.slots_redacted = slots
            await session.commit()
            state.persisted = True
    except Exception as exc:
        print(f"[Persistence] Failed to finalize call record {payload.call_id}: {exc}")


def _runtime_factory(websocket: WebSocket) -> RuntimeFactory:
    return getattr(websocket.app.state, "call_runtime_factory", PipecatCallRuntime)


async def _send_error(
    websocket: WebSocket,
    call_id: str,
    code: str,
    message: str,
    *,
    retryable: bool,
) -> None:
    await websocket.send_json(
        {
            "type": "error",
            "call_id": call_id,
            "code": code,
            "message": message,
            "retryable": retryable,
        }
    )


async def _send_frame(
    websocket: WebSocket,
    call_id: str,
    frame: Frame,
    state: WebSocketTurnState,
) -> None:
    if isinstance(frame, TranscriptionFrame):
        state.sequence += 1
        _append_transcript(
            state,
            speaker="customer",
            text=frame.text,
            node="asr",
            turn_index=state.turn_index,
        )
        await websocket.send_json(
            {
                "type": "asr_final",
                "call_id": call_id,
                "text": frame.text,
                "language": str(frame.language) if frame.language else None,
                "duration_ms": frame.metadata.get("duration_ms", state.latency["asr_ms"]),
                "sequence": state.sequence,
            }
        )
        return

    if type(frame) is TextFrame:
        state.turn_index = int(frame.metadata.get("turn_index", state.turn_index))
        _append_transcript(
            state,
            speaker="agent",
            text=frame.text,
            node=str(frame.metadata.get("node_name", "unknown")),
            turn_index=state.turn_index,
        )
        await websocket.send_json(
            {
                "type": "agent_text",
                "call_id": call_id,
                "text": frame.text,
                "node_name": frame.metadata.get("node_name", "unknown"),
                "turn_index": state.turn_index,
            }
        )
        return

    if isinstance(frame, TTSAudioRawFrame):
        await websocket.send_bytes(_AUDIO_PREFIX + frame.audio)
        return

    if isinstance(frame, LatencyFrame):
        if frame.hop == "asr":
            state.latency["asr_ms"] = frame.duration_ms
            state.latency_samples["asr"].append(frame.duration_ms)
        elif frame.hop == "llm":
            state.latency["llm_ms"] = frame.duration_ms
            state.latency_samples["llm"].append(frame.duration_ms)
        elif frame.hop == "tts":
            state.latency["tts_first_byte_ms"] = frame.duration_ms
            state.latency_samples["tts"].append(frame.duration_ms)
            await _send_turn_end(websocket, call_id, state)
        return

    if isinstance(frame, ErrorFrame):
        state.error_count += 1
        state.audio_failed = True
        await _send_error(
            websocket,
            call_id,
            "INTERNAL_ERROR",
            frame.error,
            retryable=not frame.fatal,
        )


async def _send_turn_end(websocket: WebSocket, call_id: str, state: WebSocketTurnState) -> None:
    e2e_ms = (
        state.latency["asr_ms"]
        + state.latency["llm_ms"]
        + state.latency["tts_first_byte_ms"]
    )

    # Record metrics for Prometheus /metrics endpoint
    collector = get_collector()
    collector.record("asr", state.latency["asr_ms"])
    collector.record("llm", state.latency["llm_ms"])
    collector.record("tts", state.latency["tts_first_byte_ms"])
    collector.record("e2e", e2e_ms)
    state.latency_samples["e2e"].append(e2e_ms)

    await websocket.send_json(
        {
            "type": "turn_end",
            "call_id": call_id,
            "turn_index": state.turn_index,
            "latency": {
                **state.latency,
                "e2e_ms": e2e_ms,
            },
        }
    )
    state.latency = {
        "asr_ms": 0.0,
        "llm_ms": 0.0,
        "tts_first_byte_ms": 0.0,
    }


async def _send_runtime_frames(
    websocket: WebSocket,
    call_id: str,
    runtime: CallRuntime,
    state: WebSocketTurnState,
) -> None:
    while True:
        frame = await runtime.next_frame()
        await _send_frame(websocket, call_id, frame, state)


def _initial_state_from_start(payload: StartCallPayload) -> DialogState:
    return DialogState(
        call_id=payload.call_id,
        customer_id=payload.customer_id,
        product=_normalize_product(payload.product),
        agent_name=payload.agent_name,
        lender_name=payload.lender_name,
        customer_name=payload.customer_name,
    )


def _decode_json_text(raw: str) -> dict[str, Any]:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("JSON control frame must be an object")
    return data


async def _auto_send_followup(
    payload: StartCallPayload | None,
    dialog_state: Any | None,
    outcome: str,
) -> None:
    """Auto-send follow-up message if contact info collected and outcome qualifies."""
    if not payload or not dialog_state:
        return

    # Only auto-send for qualified or callback_requested
    if outcome not in ["qualified", "callback_requested"]:
        return

    try:
        # Extract contact info from slots
        slots = dialog_state.get("slots")
        if not slots:
            return

        # SlotSet is Pydantic object, not dict
        contact_phone = slots.contact_phone
        contact_email = slots.contact_email
        contact_pref = (slots.contact_preference or "").lower()

        # Determine channel and recipient
        channel = None
        recipient = None

        if contact_pref == "whatsapp" and contact_phone:
            channel = "whatsapp"
            recipient = contact_phone
        elif contact_pref == "sms" and contact_phone:
            channel = "sms"
            recipient = contact_phone
        elif contact_pref == "email" and contact_email:
            channel = "email"
            recipient = contact_email
        elif contact_email:  # Default to email if available
            channel = "email"
            recipient = contact_email
        elif contact_phone:  # Fallback to SMS
            channel = "sms"
            recipient = contact_phone

        if not channel or not recipient:
            print(f"[Auto-send] No contact info for call {payload.call_id}")
            return

        # Load call record and send
        from .notifications import deliver_message
        from .routes.engagement import _followup_message
        from .db import AsyncSessionLocal
        from sqlmodel import select

        async with AsyncSessionLocal() as session:
            result = await session.exec(select(Call).where(Call.call_id == payload.call_id))
            call = result.first()
            if call:
                message = _followup_message(call, channel)
                subject = f"{call.product.replace('_', ' ').title()} Follow-up" if channel == "email" else None
                deliver_message(channel, message, recipient, subject=subject)
                print(f"[Auto-send] Sent {channel} to {recipient} for call {payload.call_id}")
    except Exception as exc:
        print(f"[Auto-send] Failed for call {payload.call_id if payload else 'unknown'}: {exc}")


@router.websocket("/ws/call/{call_id}")
async def call_websocket(websocket: WebSocket, call_id: str) -> None:
    await websocket.accept()

    runtime: CallRuntime | None = None
    sender_task: asyncio.Task[None] | None = None
    db_session: Any | None = None
    state = WebSocketTurnState()
    started_payload: StartCallPayload | None = None
    final_status = "dropped"
    final_outcome = "dropped"

    try:
        first_message = await websocket.receive_json()
        started_payload = StartCallPayload.model_validate(first_message)
        if started_payload.type != "start_call":
            raise ValueError("First message must be start_call")
        if started_payload.call_id != call_id:
            raise ValueError("Path call_id and payload call_id do not match")

        # Phase 2: Support all 10 products.
        if _normalize_product(started_payload.product) not in _VALID_PRODUCTS:
            raise ValueError(
                f"Invalid product: {started_payload.product}. "
                f"Must be one of: {', '.join(sorted(_VALID_PRODUCTS))}"
            )

        await _create_call_record(started_payload, state)

        # Create DB session for nudge generation
        db_session = AsyncSessionLocal()

        runtime = _runtime_factory(websocket)(_initial_state_from_start(started_payload), db_session=db_session)
        if hasattr(runtime, "set_language"):
            runtime.set_language(started_payload.language)
        await runtime.start()

        await websocket.send_json(
            {
                "type": "call_accepted",
                "call_id": call_id,
                "session_token": secrets.token_urlsafe(16),
            }
        )

        sender_task = asyncio.create_task(_send_runtime_frames(websocket, call_id, runtime, state))

        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                raise WebSocketDisconnect()

            if message.get("bytes") is not None:
                state.sequence += 1
                await websocket.send_json(
                    {
                        "type": "asr_partial",
                        "call_id": call_id,
                        "text": "",
                        "sequence": state.sequence,
                    }
                )
                await runtime.queue_audio(message["bytes"])
                continue

            if message.get("text") is None:
                await _send_error(
                    websocket,
                    call_id,
                    "PROTOCOL_ERROR",
                    "Unsupported WebSocket frame",
                    retryable=False,
                )
                continue

            try:
                data = _decode_json_text(message["text"])
            except (json.JSONDecodeError, ValueError) as exc:
                await _send_error(websocket, call_id, "PROTOCOL_ERROR", str(exc), retryable=False)
                continue

            event_type = data.get("type")
            if event_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif event_type == "text_input":
                # Handle typed contact info (email/phone) - inject as TranscriptionFrame
                text = data.get("text", "").strip()
                if text and runtime and runtime._task:
                    from pipecat.frames.frames import TranscriptionFrame
                    # Queue transcription frame directly (bypass ASR)
                    await runtime._task.queue_frame(
                        TranscriptionFrame(text=text, user_id=call_id, timestamp=time.time()),
                        FrameDirection.DOWNSTREAM,
                    )
                    await websocket.send_json({
                        "type": "asr_final",
                        "text": text,
                        "sequence": state.turn_index,
                    })
            elif event_type == "end_call":
                end_payload = EndCallPayload.model_validate(data)
                if end_payload.call_id != call_id:
                    await _send_error(
                        websocket,
                        call_id,
                        "PROTOCOL_ERROR",
                        "end_call call_id does not match path",
                        retryable=False,
                    )
                    continue
                await runtime.stop()
                duration_s = time.perf_counter() - state.started_at
                final_status = "completed"
                final_outcome = await _resolve_outcome(runtime, fallback="dropped")
                dialog_state = await runtime.get_dialog_state()
                dialog_turn_count = int(_state_get(dialog_state, "turn_index", state.turn_index))
                call_ended_msg = {
                    "type": "call_ended",
                    "call_id": call_id,
                    "outcome": final_outcome,
                    "duration_s": duration_s,
                    "turn_count": max(state.turn_index, dialog_turn_count),
                }
                await _finalize_call_record(
                    started_payload,
                    state,
                    status=final_status,
                    outcome=final_outcome,
                    dialog_state=dialog_state,
                )

                # Auto-send follow-up if contact info collected
                await _auto_send_followup(started_payload, dialog_state, final_outcome)

                print(f"[WebSocket] Sending call_ended: {call_ended_msg}")
                await websocket.send_json(call_ended_msg)
                await websocket.close()
                break
            else:
                await _send_error(
                    websocket,
                    call_id,
                    "PROTOCOL_ERROR",
                    f"Unknown event type: {event_type}",
                    retryable=False,
                )

    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        await _send_error(websocket, call_id, "PROTOCOL_ERROR", str(exc), retryable=False)
        await websocket.close(code=1008)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        state.error_count += 1
        await _send_error(websocket, call_id, "INTERNAL_ERROR", str(exc), retryable=False)
        await websocket.close(code=1011)
    finally:
        if sender_task is not None:
            sender_task.cancel()
            await asyncio.gather(sender_task, return_exceptions=True)
        if runtime is not None and (started_payload is None or started_payload.call_id == call_id):
            await runtime.close()
        if db_session is not None:
            await db_session.close()
        await _finalize_call_record(
            started_payload,
            state,
            status=final_status,
            outcome=final_outcome,
        )


@router.post("/call/outbound")
async def create_outbound_call(payload: OutboundCallPayload):
    """Initiate an outbound call via Twilio."""
    return await initiate_outbound_call(payload)


@router.post("/call/webhook")
async def twilio_webhook():
    """Webhook endpoint for Twilio incoming calls.
    
    Twilio calls this when a call comes in to our phone number.
    We respond with TwiML that tells Twilio to connect to our streaming WebSocket.
    """
    call_id = f"twilio_{secrets.token_urlsafe(8)}"
    api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
    
    # Generate TwiML that connects to our WebSocket for streaming
    response = VoiceResponse()
    response.connect().stream(url=_twilio_stream_url(api_base_url, call_id))
    
    return Response(content=response.to_xml(), media_type="application/xml")


async def initiate_outbound_call(payload: OutboundCallPayload):
    """Initiate an outbound call using Twilio."""
    try:
        account_sid = os.environ["TWILIO_ACCOUNT_SID"]
        auth_token = os.environ["TWILIO_AUTH_TOKEN"]
        twilio_number = os.environ["TWILIO_PHONE_NUMBER"]
        api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
    except KeyError as e:
        raise HTTPException(status_code=500, detail=f"Missing Twilio environment variable: {e}")

    customer_phone = _normalize_phone_number(payload.customer_phone)
    client = Client(account_sid, auth_token)

    # Generate a unique call ID
    call_id = f"outbound_{secrets.token_urlsafe(8)}"

    # Create TwiML for the call
    twiml = VoiceResponse()
    twiml.connect().stream(url=_twilio_stream_url(api_base_url, call_id))

    # Initiate the call
    try:
        call = client.calls.create(
            to=customer_phone,
            from_=twilio_number,
            twiml=str(twiml),
        )
    except TwilioRestException as exc:
        message = exc.msg or str(exc)
        if exc.code:
            message = f"Twilio error {exc.code}: {message}"
        raise HTTPException(status_code=exc.status or 502, detail=message) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to initiate Twilio call: {exc}",
        ) from exc

    _OUTBOUND_CALL_CONTEXT[call_id] = payload

    return {"call_sid": call.sid, "call_id": call_id, "to": customer_phone}


@router.websocket("/ws/twilio/{call_id}")
async def twilio_websocket(websocket: WebSocket, call_id: str):
    """Handle Twilio streaming WebSocket for outbound calls."""
    await websocket.accept()

    runtime: CallRuntime | None = None
    frame_task: asyncio.Task[None] | None = None
    state = WebSocketTurnState()
    started_payload: StartCallPayload | None = None
    final_status = "dropped"
    final_outcome = "dropped"
    try:
        context = _OUTBOUND_CALL_CONTEXT.get(call_id)
        product = context.product if context else "personal_loan"
        agent_name = context.agent_name if context else "Priya"
        lender_name = context.lender_name if context else "Demo Bank"
        customer_name = context.customer_name if context else "Customer"

        started_payload = StartCallPayload(
            type="start_call",
            call_id=call_id,
            customer_id="twilio_customer",
            product=product,
            language=context.language if context else "en-IN",
            agent_name=agent_name,
            lender_name=lender_name,
            customer_name=customer_name,
        )
        await _create_call_record(started_payload, state)

        runtime = _runtime_factory(websocket)(_initial_state_from_start(
            started_payload
        ))
        if hasattr(runtime, "set_language"):
            runtime.set_language(started_payload.language)
        await runtime.start()

        # Handle Twilio streaming protocol
        while True:
            message = await websocket.receive()
            if message.get("text"):
                data = json.loads(message["text"])
                event_type = data.get("event")
                if event_type == "connected":
                    print(f"[Twilio] Media stream connected: {call_id}")
                elif event_type == "media":
                    # Decode mulaw audio
                    mulaw_data = base64.b64decode(data["media"]["payload"])
                    # Twilio sends 8 kHz mulaw; the pipeline expects 16 kHz PCM.
                    pcm_data = _twilio_mulaw_to_pcm_16k(mulaw_data)
                    await runtime.queue_audio(pcm_data)
                elif event_type == "start":
                    state.stream_sid = data.get("streamSid") or data.get("start", {}).get("streamSid")
                    print(f"[Twilio] Call started: {call_id}")
                    if frame_task is None:
                        frame_task = asyncio.create_task(
                            _process_twilio_frames(websocket, call_id, runtime, state)
                        )
                elif event_type == "dtmf":
                    digit = data.get("dtmf", {}).get("digit")
                    print(f"[Twilio] Ignoring inbound DTMF {digit!r} for {call_id}")
                elif event_type == "mark":
                    continue
                elif event_type == "stop":
                    final_status = "completed"
                    await runtime.stop()
                    final_outcome = await _resolve_outcome(runtime, fallback="dropped")
                    print(f"[Twilio] Call ended: {call_id}")
                    break
                else:
                    print(f"[Twilio] Ignoring unsupported event {event_type!r} for {call_id}")
            elif message.get("bytes"):
                # Handle binary audio data if sent differently
                pass

    except Exception as exc:
        state.error_count += 1
        print(f"[Twilio] Exception: {exc}")
    finally:
        if frame_task:
            frame_task.cancel()
            await asyncio.gather(frame_task, return_exceptions=True)
        dialog_state = None
        if runtime:
            try:
                dialog_state = await runtime.get_dialog_state()
            except Exception:
                dialog_state = None
        if runtime:
            await runtime.close()
        await _finalize_call_record(
            started_payload,
            state,
            status=final_status,
            outcome=final_outcome,
            dialog_state=dialog_state,
        )
        _OUTBOUND_CALL_CONTEXT.pop(call_id, None)


async def _process_twilio_frames(
    websocket: WebSocket,
    call_id: str,
    runtime: CallRuntime,
    state: WebSocketTurnState,
) -> None:
    """Process frames from the pipeline and send to Twilio."""
    try:
        while True:
            frame = await runtime.next_frame()
            await _send_twilio_frame(websocket, call_id, frame, state)
    except Exception as exc:
        print(f"[Twilio] Frame processing error: {exc}")


async def _send_twilio_frame(
    websocket: WebSocket,
    call_id: str,
    frame: Frame,
    state: WebSocketTurnState,
) -> None:
    """Send frame to Twilio in the correct format."""
    if isinstance(frame, TTSAudioRawFrame):
        if not state.stream_sid:
            print(f"[Twilio] Dropping outbound audio before start event: {call_id}")
            return

        # Twilio expects raw 8 kHz audio/x-mulaw with the stream SID.
        mulaw_data = _pcm_16k_to_twilio_mulaw(frame.audio)
        state.outbound_chunk += 1
        media_message = {
            "event": "media",
            "streamSid": state.stream_sid,
            "media": {
                "payload": base64.b64encode(mulaw_data).decode("utf-8"),
            },
        }
        await websocket.send_json(media_message)
    elif isinstance(frame, TranscriptionFrame):
        _append_transcript(
            state,
            speaker="customer",
            text=frame.text,
            node="twilio_asr",
            turn_index=state.turn_index,
        )
        # For now, just log transcriptions
        print(f"[Twilio] Transcription: {frame.text}")
    elif isinstance(frame, TextFrame):
        state.turn_index = int(frame.metadata.get("turn_index", state.turn_index))
        _append_transcript(
            state,
            speaker="agent",
            text=frame.text,
            node=str(frame.metadata.get("node_name", "unknown")),
            turn_index=state.turn_index,
        )
        # Log agent text
        print(f"[Twilio] Agent: {frame.text}")
    elif isinstance(frame, LatencyFrame):
        if frame.hop in state.latency_samples:
            state.latency_samples[frame.hop].append(frame.duration_ms)
    elif isinstance(frame, ErrorFrame):
        state.error_count += 1
        state.audio_failed = True
        print(f"[Twilio] Error: {frame.error}")
    # Handle other frame types as needed


def _twilio_mulaw_to_pcm_16k(mulaw_bytes: bytes) -> bytes:
    """Convert Twilio 8 kHz mulaw audio to 16 kHz PCM for the pipeline."""
    import audioop

    pcm_8k = audioop.ulaw2lin(mulaw_bytes, 2)
    pcm_16k, _ = audioop.ratecv(pcm_8k, 2, 1, 8000, 16000, None)
    return pcm_16k


def _pcm_16k_to_twilio_mulaw(pcm_bytes: bytes) -> bytes:
    """Convert 16 kHz PCM pipeline audio to Twilio 8 kHz mulaw."""
    import audioop

    pcm_8k, _ = audioop.ratecv(pcm_bytes, 2, 1, 16000, 8000, None)
    return audioop.lin2ulaw(pcm_8k, 2)
