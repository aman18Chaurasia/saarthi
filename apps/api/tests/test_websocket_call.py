"""WebSocket protocol tests for /ws/call/{call_id}.

External services are mocked at the runtime boundary. These tests validate the
ADR 0002 wire protocol without calling Groq, ElevenLabs, Pipecat, or Postgres.
"""
from __future__ import annotations

import asyncio
import base64
import json
from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pipecat.frames.frames import TTSAudioRawFrame, TextFrame, TranscriptionFrame

from apps.api.frames import LatencyFrame
from apps.api.main import app
from apps.api import websocket_call as websocket_call_module


class _FakeRuntime:
    def __init__(self, initial_state: Any) -> None:
        self.initial_state = initial_state
        self.started = False
        self.stopped = False
        self.closed = False
        self.audio_chunks: list[bytes] = []
        self.dialog_state: Any | None = None
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

    async def get_dialog_state(self) -> Any | None:
        return self.dialog_state


class _QuietRuntime(_FakeRuntime):
    async def queue_audio(self, audio: bytes) -> None:
        self.audio_chunks.append(audio)


class _QualifiedRuntime(_QuietRuntime):
    def __init__(self, initial_state: Any) -> None:
        super().__init__(initial_state)
        self.dialog_state = {
            "product": "personal_loan",
            "turn_index": 6,
            "slots": {
                "monthly_income_inr": 50000,
                "loan_purpose": "travel",
                "consent_given": True,
            },
        }


@pytest.fixture()
def runtime_factory(monkeypatch: pytest.MonkeyPatch) -> Callable[[type[_FakeRuntime]], list[_FakeRuntime]]:
    monkeypatch.setenv("SAARTHI_DISABLE_CALL_PERSISTENCE", "1")
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


def test_end_call_derives_non_dropped_outcome_from_dialog_state(
    runtime_factory: Callable[[type[_FakeRuntime]], list[_FakeRuntime]],
) -> None:
    runtime_factory(_QualifiedRuntime)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/call/call_ws_001") as ws:
            ws.send_json(_start_payload())
            assert ws.receive_json()["type"] == "call_accepted"

            ws.send_json({"type": "end_call", "call_id": "call_ws_001", "reason": "user_hangup"})
            ended = ws.receive_json()

            assert ended["type"] == "call_ended"
            assert ended["outcome"] == "qualified"
            assert ended["turn_count"] == 6


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


def _outbound_payload(**overrides: str) -> dict[str, str]:
    payload = {
        "customer_phone": "+91 98765 43210",
        "product": "personal_loan",
        "agent_name": "Priya",
        "lender_name": "Demo Bank",
        "customer_name": "Rahul",
    }
    payload.update(overrides)
    return payload


def _set_twilio_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC00000000000000000000000000000000")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO_PHONE_NUMBER", "+15551234567")
    monkeypatch.setenv("API_BASE_URL", "https://example.ngrok-free.dev")


def test_outbound_call_normalizes_phone_and_uses_public_stream_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_twilio_env(monkeypatch)
    created: dict[str, str] = {}

    class _FakeCalls:
        def create(self, **kwargs: str) -> Any:
            created.update(kwargs)
            return type("Call", (), {"sid": "CA123"})()

    class _FakeClient:
        def __init__(self, account_sid: str, auth_token: str) -> None:
            assert account_sid.startswith("AC")
            assert auth_token == "token"
            self.calls = _FakeCalls()

    monkeypatch.setattr(websocket_call_module, "Client", _FakeClient)

    with TestClient(app) as client:
        response = client.post("/call/outbound", json=_outbound_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["call_sid"] == "CA123"
    assert body["to"] == "+919876543210"
    assert created["to"] == "+919876543210"
    assert "wss://example.ngrok-free.dev/ws/twilio/outbound_" in created["twiml"]


def test_outbound_call_rejects_invalid_phone(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_twilio_env(monkeypatch)

    with TestClient(app) as client:
        response = client.post(
            "/call/outbound",
            json=_outbound_payload(customer_phone="+91 098"),
        )

    assert response.status_code == 400
    assert "E.164" in response.json()["detail"]


def test_outbound_call_rejects_localhost_stream_url(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_twilio_env(monkeypatch)
    monkeypatch.setenv("API_BASE_URL", "http://localhost:8000")

    with TestClient(app) as client:
        response = client.post("/call/outbound", json=_outbound_payload())

    assert response.status_code == 400
    assert "ngrok" in response.json()["detail"]


def test_outbound_call_allows_browser_cors_preflight() -> None:
    with TestClient(app) as client:
        response = client.options(
            "/call/outbound",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


@pytest.mark.asyncio
async def test_twilio_outbound_audio_includes_stream_sid() -> None:
    sent: list[dict[str, Any]] = []

    class _FakeWebSocket:
        async def send_json(self, payload: dict[str, Any]) -> None:
            sent.append(payload)

    state = websocket_call_module.WebSocketTurnState(stream_sid="MZ123")
    frame = TTSAudioRawFrame(audio=b"\x00\x00" * 160, sample_rate=16000, num_channels=1)

    await websocket_call_module._send_twilio_frame(_FakeWebSocket(), "call_001", frame, state)

    assert len(sent) == 1
    assert sent[0]["event"] == "media"
    assert sent[0]["streamSid"] == "MZ123"
    assert sent[0]["media"]["payload"]


def test_twilio_websocket_ignores_dtmf_and_only_queues_media(
    runtime_factory: Callable[[type[_FakeRuntime]], list[_FakeRuntime]],
) -> None:
    created = runtime_factory(_QuietRuntime)
    websocket_call_module._OUTBOUND_CALL_CONTEXT["outbound_test"] = (
        websocket_call_module.OutboundCallPayload(
            customer_phone="+919876543210",
            product="personal_loan",
            agent_name="Priya",
            lender_name="Demo Bank",
            customer_name="Rahul",
        )
    )

    mulaw_payload = base64.b64encode(b"\xff" * 160).decode("utf-8")

    with TestClient(app) as client:
        with client.websocket_connect("/ws/twilio/outbound_test") as ws:
            ws.send_text(json.dumps({"event": "connected", "protocol": "Call", "version": "1.0.0"}))
            ws.send_text(
                json.dumps(
                    {
                        "event": "start",
                        "streamSid": "MZ123",
                        "start": {"streamSid": "MZ123"},
                    }
                )
            )
            ws.send_text(
                json.dumps(
                    {
                        "event": "dtmf",
                        "streamSid": "MZ123",
                        "dtmf": {"track": "inbound_track", "digit": "1"},
                    }
                )
            )
            ws.send_text(
                json.dumps(
                    {
                        "event": "media",
                        "streamSid": "MZ123",
                        "media": {"payload": mulaw_payload},
                    }
                )
            )
            ws.send_text(
                json.dumps(
                    {
                        "event": "stop",
                        "streamSid": "MZ123",
                        "stop": {"callSid": "CA123"},
                    }
                )
            )

    assert len(created) == 1
    assert len(created[0].audio_chunks) == 1
    assert len(created[0].audio_chunks[0]) > 0
