"""WebSocket protocol tests for /ws/call/{call_id}.

External services are mocked at the runtime boundary. These tests validate the
ADR 0002 wire protocol without calling Groq, ElevenLabs, Pipecat, or Postgres.
"""
from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pipecat.frames.frames import TTSAudioRawFrame, TextFrame, TranscriptionFrame

from frames import LatencyFrame
from main import app


class _FakeRuntime:
    def __init__(self, initial_state: Any) -> None:
        self.initial_state = initial_state
        self.started = False
        self.stopped = False
        self.closed = False
        self.audio_chunks: list[bytes] = []
        self._frames: asyncio.Queue = asyncio.Queue()

    async def start(self) -> None:
        self.started = True

    async def queue_audio(self, audio: bytes) -> None:
        self.audio_chunks.append(audio)

        text_frame = TextFrame(text="Income kitni hai?")
        text_frame.metadata["node_name"] = "qualify"
        text_frame.metadata["turn_index"] = 2

        transcription = TranscriptionFrame(
            text="Haan, main Priya hoon",
            user_id=self.initial_state.call_id,
            timestamp="0",
            finalized=True,
        )
        transcription.metadata["duration_ms"] = 11.0

        await self._frames.put(transcription)
        await self._frames.put(LatencyFrame(hop="asr", duration_ms=11.0))
        await self._frames.put(text_frame)
        await self._frames.put(LatencyFrame(hop="llm", duration_ms=22.0))
        await self._frames.put(
            TTSAudioRawFrame(audio=b"\x10\x20", sample_rate=16000, num_channels=1)
        )
        await self._frames.put(LatencyFrame(hop="tts", duration_ms=33.0))

    async def next_frame(self):
        return await self._frames.get()

    async def stop(self) -> None:
        self.stopped = True

    async def close(self) -> None:
        self.closed = True


class _QuietRuntime(_FakeRuntime):
    async def queue_audio(self, audio: bytes) -> None:
        self.audio_chunks.append(audio)


@pytest.fixture()
def runtime_factory() -> Callable[[type[_FakeRuntime]], list[_FakeRuntime]]:
    created: list[_FakeRuntime] = []

    def install(runtime_cls: type[_FakeRuntime] = _FakeRuntime) -> list[_FakeRuntime]:
        def factory(initial_state: Any) -> _FakeRuntime:
            runtime = runtime_cls(initial_state)
            created.append(runtime)
            return runtime

        app.state.call_runtime_factory = factory
        return created

    yield install

    if hasattr(app.state, "call_runtime_factory"):
        delattr(app.state, "call_runtime_factory")


def _start_payload(call_id: str = "call_ws_001") -> dict[str, str]:
    return {
        "type": "start_call",
        "call_id": call_id,
        "customer_id": "cust_001",
        "product": "personal_loan",
        "agent_name": "Bunty",
        "lender_name": "Demo Bank",
        "customer_name": "Priya",
    }


def test_start_call_accepts_and_ping_pongs(
    runtime_factory: Callable[[type[_FakeRuntime]], list[_FakeRuntime]],
) -> None:
    created = runtime_factory(_QuietRuntime)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/call/call_ws_001") as ws:
            ws.send_json(_start_payload())
            accepted = ws.receive_json()

            assert accepted["type"] == "call_accepted"
            assert accepted["call_id"] == "call_ws_001"
            assert accepted["session_token"]

            ws.send_json({"type": "ping"})
            assert ws.receive_json() == {"type": "pong"}

    assert created[0].started is True
    assert created[0].initial_state.customer_name == "Priya"


def test_binary_audio_is_forwarded_and_pipeline_frames_are_mapped(
    runtime_factory: Callable[[type[_FakeRuntime]], list[_FakeRuntime]],
) -> None:
    created = runtime_factory(_FakeRuntime)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/call/call_ws_001") as ws:
            ws.send_json(_start_payload())
            assert ws.receive_json()["type"] == "call_accepted"

            ws.send_bytes(b"\x00" * 640)

            messages: list[dict | bytes] = []
            while not any(
                isinstance(item, dict) and item.get("type") == "turn_end" for item in messages
            ):
                raw = ws.receive()
                if "bytes" in raw and raw["bytes"] is not None:
                    messages.append(raw["bytes"])
                elif "text" in raw and raw["text"] is not None:
                    messages.append(json.loads(raw["text"]))

    assert created[0].audio_chunks == [b"\x00" * 640]

    json_events = [item for item in messages if isinstance(item, dict)]
    event_types = [item["type"] for item in json_events]
    assert "asr_partial" in event_types
    assert "asr_final" in event_types
    assert "agent_text" in event_types
    assert "turn_end" in event_types

    agent_text = next(item for item in json_events if item["type"] == "agent_text")
    assert agent_text["text"] == "Income kitni hai?"
    assert agent_text["node_name"] == "qualify"
    assert agent_text["turn_index"] == 2

    asr_final = next(item for item in json_events if item["type"] == "asr_final")
    assert asr_final["text"] == "Haan, main Priya hoon"
    assert asr_final["duration_ms"] == 11.0

    audio_events = [item for item in messages if isinstance(item, bytes)]
    assert audio_events == [b"\x01\x10\x20"]

    turn_end = next(item for item in json_events if item["type"] == "turn_end")
    assert turn_end["latency"] == {
        "asr_ms": 11.0,
        "llm_ms": 22.0,
        "tts_first_byte_ms": 33.0,
        "e2e_ms": 66.0,
    }


def test_end_call_stops_runtime_and_emits_call_ended(
    runtime_factory: Callable[[type[_FakeRuntime]], list[_FakeRuntime]],
) -> None:
    created = runtime_factory(_QuietRuntime)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/call/call_ws_001") as ws:
            ws.send_json(_start_payload())
            assert ws.receive_json()["type"] == "call_accepted"

            ws.send_json({"type": "end_call", "call_id": "call_ws_001", "reason": "user_hangup"})
            ended = ws.receive_json()

            assert ended["type"] == "call_ended"
            assert ended["call_id"] == "call_ws_001"
            assert ended["outcome"] == "dropped"
            assert ended["duration_s"] >= 0.0

    assert created[0].stopped is True


def test_start_call_call_id_mismatch_returns_protocol_error(
    runtime_factory: Callable[[type[_FakeRuntime]], list[_FakeRuntime]],
) -> None:
    created = runtime_factory(_QuietRuntime)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/call/call_ws_001") as ws:
            ws.send_json(_start_payload(call_id="different"))
            error = ws.receive_json()

            assert error["type"] == "error"
            assert error["code"] == "PROTOCOL_ERROR"
            assert error["retryable"] is False
            assert "call_id" in error["message"]

    assert created == []


def test_unknown_control_event_returns_protocol_error(
    runtime_factory: Callable[[type[_FakeRuntime]], list[_FakeRuntime]],
) -> None:
    runtime_factory(_QuietRuntime)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/call/call_ws_001") as ws:
            ws.send_json(_start_payload())
            assert ws.receive_json()["type"] == "call_accepted"

            ws.send_json({"type": "bogus"})
            error = ws.receive_json()

            assert error["type"] == "error"
            assert error["code"] == "PROTOCOL_ERROR"
            assert error["retryable"] is False
