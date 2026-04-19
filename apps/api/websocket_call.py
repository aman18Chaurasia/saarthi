"""FastAPI WebSocket endpoint for Phase 1 browser voice calls.

The endpoint owns the wire protocol from ADR 0002 section 3 and delegates
audio/dialog work to a per-call runtime. Tests inject a fake runtime so no Groq,
ElevenLabs, or Postgres calls are made.
"""
from __future__ import annotations

import asyncio
import json
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError
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

from dialog.personal_loan.state import DialogState
from frames import LatencyFrame
from pipeline import build_pipeline

router = APIRouter()

_AUDIO_PREFIX = b"\x01"
_AUDIO_SAMPLE_RATE = 16000
_AUDIO_CHANNELS = 1


class StartCallPayload(BaseModel):
    type: str
    call_id: str
    customer_id: str
    product: str
    agent_name: str
    lender_name: str
    customer_name: str


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


class PipecatCallRuntime:
    """Runtime adapter between the WebSocket endpoint and Pipecat PipelineTask."""

    def __init__(self, initial_state: DialogState) -> None:
        self._initial_state = initial_state
        self._outgoing: asyncio.Queue[Frame] = asyncio.Queue()
        self._runner_task: asyncio.Task[None] | None = None
        self._task: PipelineTask | None = None

    async def start(self) -> None:
        pipeline, graph_app, graph_config = build_pipeline(
            self._initial_state.call_id,
            self._initial_state,
        )

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


RuntimeFactory = Callable[[DialogState], CallRuntime]


@dataclass
class WebSocketTurnState:
    started_at: float = field(default_factory=time.perf_counter)
    sequence: int = 0
    turn_index: int = 0
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
        elif frame.hop == "llm":
            state.latency["llm_ms"] = frame.duration_ms
        elif frame.hop == "tts":
            state.latency["tts_first_byte_ms"] = frame.duration_ms
            await _send_turn_end(websocket, call_id, state)
        return

    if isinstance(frame, ErrorFrame):
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
        product=payload.product,
        agent_name=payload.agent_name,
        lender_name=payload.lender_name,
        customer_name=payload.customer_name,
    )


def _decode_json_text(raw: str) -> dict[str, Any]:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("JSON control frame must be an object")
    return data


@router.websocket("/ws/call/{call_id}")
async def call_websocket(websocket: WebSocket, call_id: str) -> None:
    await websocket.accept()

    runtime: CallRuntime | None = None
    sender_task: asyncio.Task[None] | None = None
    state = WebSocketTurnState()
    started_payload: StartCallPayload | None = None

    try:
        first_message = await websocket.receive_json()
        started_payload = StartCallPayload.model_validate(first_message)
        if started_payload.type != "start_call":
            raise ValueError("First message must be start_call")
        if started_payload.call_id != call_id:
            raise ValueError("Path call_id and payload call_id do not match")
        if started_payload.product != "personal_loan":
            raise ValueError("Only product=personal_loan is supported in Phase 1")

        runtime = _runtime_factory(websocket)(_initial_state_from_start(started_payload))
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
                call_ended_msg = {
                    "type": "call_ended",
                    "call_id": call_id,
                    "outcome": "dropped",
                    "duration_s": duration_s,
                    "turn_count": state.turn_index,
                }
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
        await _send_error(websocket, call_id, "INTERNAL_ERROR", str(exc), retryable=False)
        await websocket.close(code=1011)
    finally:
        if sender_task is not None:
            sender_task.cancel()
            await asyncio.gather(sender_task, return_exceptions=True)
        if runtime is not None and (started_payload is None or started_payload.call_id == call_id):
            await runtime.close()
