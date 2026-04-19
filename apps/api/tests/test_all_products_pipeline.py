"""Test that all 10 products can build pipelines successfully."""
import pytest
from pipeline import build_pipeline


PRODUCTS = [
    "personal_loan", "home_loan", "education_loan", "gold_loan", "credit_card",
    "unsecured_loan", "lap_secured", "commercial_vehicle", "four_wheeler", "msme_business"
]


@pytest.mark.parametrize("product", PRODUCTS)
async def test_product_pipeline_builds(product, monkeypatch):
    """Verify pipeline builds for each product without errors."""
    # Mock GROQ_API_KEY env var
    monkeypatch.setenv("GROQ_API_KEY", "test-key-12345")
    # Import the product's DialogState dynamically
    state_module = __import__(f"dialog.{product}.state", fromlist=["DialogState"])
    DialogState = state_module.DialogState

    # Create initial state
    initial_state = DialogState(
        call_id=f"test-{product}",
        customer_id="cust-001",
        product=product,
        agent_name="Test Agent",
        lender_name="Test Bank",
        customer_name="Test Customer"
    )

    # Mock LLM function
    from dialog.personal_loan.schema import StructuredAgentResponse

    async def mock_llm_fn(messages, node_name, asr_text):
        return StructuredAgentResponse(
            classified_intent="unclear",
            slots_extracted={},
            agent_turn_text="Test response"
        )

    # Mock TTS provider
    class MockTTS:
        async def text_to_speech(self, text):
            # Return silent PCM
            return b"\x00\x00" * 1600  # 100ms of silence

    # Build pipeline
    pipeline, app, config = build_pipeline(
        call_id=initial_state.call_id,
        initial_state=initial_state,
        llm_fn=mock_llm_fn,
        tts_provider=MockTTS()
    )

    # Verify pipeline structure
    assert pipeline is not None
    assert app is not None
    assert config["configurable"]["thread_id"] == initial_state.call_id

    # Verify graph can invoke opener
    opener_state = await app.ainvoke(initial_state.model_dump(), config)
    assert opener_state is not None
    assert opener_state["current_node"] in ["identity_confirm", "opener"]  # Opener advances or stays
