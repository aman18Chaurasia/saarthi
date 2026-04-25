"""Tests for the LiveConversationSupervisor wrapper."""
from __future__ import annotations

import pytest
from dialog.live_supervisor import build_supervised_llm_fn


class MockResponse:
    def __init__(self, text="mock"):
        self.agent_turn_text = text
        self.slots_extracted = {}


@pytest.mark.asyncio
async def test_supervisor_wraps_llm():
    """Verify build_supervised_llm_fn wraps the base LLM and modifies messages."""
    base_called = False
    
    async def mock_base_llm(messages, node_name, asr_text):
        nonlocal base_called
        base_called = True
        
        # Verify compliance guidance was injected
        has_compliance = any("COMPLIANCE RULES" in m.get("content", "") for m in messages if m.get("role") == "system")
        assert has_compliance, "Compliance system message not injected by supervisor"
        
        return MockResponse()

    wrapped_llm = build_supervised_llm_fn(
        call_id="test_sup_1",
        product="personal_loan",
        base_llm_fn=mock_base_llm,
    )
    
    messages = [{"role": "system", "content": "base system"}]
    await wrapped_llm(messages, "opener", "hello")
    
    assert base_called, "Base LLM was not called by the supervisor wrapper"


@pytest.mark.asyncio
async def test_supervisor_calls_rag():
    """Verify RAG is triggered for product questions."""
    rag_called = False
    
    async def mock_rag(query, product, top_k):
        nonlocal rag_called
        rag_called = True
        return "RAG Context: 10% interest"
        
    async def mock_base_llm(messages, node_name, asr_text):
        # Verify RAG context was injected
        has_rag = any("RAG Context: 10% interest" in m.get("content", "") for m in messages if m.get("role") == "system")
        assert has_rag, "RAG context not injected by supervisor"
        return MockResponse()
        
    wrapped_llm = build_supervised_llm_fn(
        call_id="test_sup_2",
        product="personal_loan",
        base_llm_fn=mock_base_llm,
        rag_fn=mock_rag,
    )
    
    # "kya" is a trigger word
    await wrapped_llm([{"role": "system", "content": "sys"}], "qualify", "interest rate kya hai")
    
    assert rag_called, "RAG function was not called for a question"
