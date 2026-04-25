from __future__ import annotations

import sys
import types

import pytest

from apps.api import pipeline as pipeline_module
from dialog.personal_loan.schema import StructuredAgentResponse
from dialog.personal_loan.state import DialogState


async def _mock_transcribe_fn(_: bytes) -> str:
    return "haan"


async def _mock_llm_fn(
    messages: list[dict[str, str]],
    node_name: str,
    asr_text: str,
) -> StructuredAgentResponse:
    del messages, node_name, asr_text
    return StructuredAgentResponse(
        classified_intent="unclear",
        slots_extracted={},
        agent_turn_text="Test response",
    )


def _initial_state() -> DialogState:
    return DialogState(
        call_id="test-call",
        customer_id="cust-001",
        product="personal_loan",
        agent_name="Test Agent",
        lender_name="Test Bank",
        customer_name="Test Customer",
    )


@pytest.mark.asyncio
async def test_build_pipeline_uses_tts_factory_when_provider_not_injected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel_provider = object()

    def _fake_get_tts_provider() -> object:
        return sentinel_provider

    class CapturingTTSProcessor(pipeline_module.TTSProcessor):
        captured_provider: object | None = None

        def __init__(self, tts_provider: object, voice_id: str | None = None) -> None:
            type(self).captured_provider = tts_provider
            super().__init__(tts_provider=tts_provider, voice_id=voice_id)

    fake_factory = types.ModuleType("voice.factory")
    fake_factory.get_tts_provider = _fake_get_tts_provider

    monkeypatch.setitem(sys.modules, "voice.factory", fake_factory)
    monkeypatch.setattr(pipeline_module, "TTSProcessor", CapturingTTSProcessor)

    pipeline_module.build_pipeline(
        call_id="test-call",
        initial_state=_initial_state(),
        transcribe_fn=_mock_transcribe_fn,
        llm_fn=_mock_llm_fn,
    )

    assert CapturingTTSProcessor.captured_provider is sentinel_provider
