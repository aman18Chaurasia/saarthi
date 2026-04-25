"""Regression tests for SAARTHI product conversations.

Verifies that all 10 products can successfully navigate their graph from
opener to close using a simulated LLM.
"""
from __future__ import annotations

import pytest

from dialog.home_loan.graph import build_graph as hl_build_graph
from dialog.personal_loan.graph import build_graph as pl_build_graph
from dialog.gold_loan.graph import build_graph as gl_build_graph
from dialog.credit_card.graph import build_graph as cc_build_graph
from dialog.education_loan.graph import build_graph as el_build_graph
from dialog.lap_secured.graph import build_graph as ls_build_graph
from dialog.commercial_vehicle.graph import build_graph as cv_build_graph
from dialog.four_wheeler.graph import build_graph as fw_build_graph
from dialog.msme_business.graph import build_graph as mb_build_graph
from dialog.unsecured_loan.graph import build_graph as ul_build_graph


PRODUCT_BUILDERS = {
    "home_loan": hl_build_graph,
    "personal_loan": pl_build_graph,
    "gold_loan": gl_build_graph,
    "credit_card": cc_build_graph,
    "education_loan": el_build_graph,
    "lap_secured": ls_build_graph,
    "commercial_vehicle": cv_build_graph,
    "four_wheeler": fw_build_graph,
    "msme_business": mb_build_graph,
    "unsecured_loan": ul_build_graph,
}

ALL_PRODUCTS = list(PRODUCT_BUILDERS.keys())


class MockStructuredAgentResponse:
    def __init__(self, intent, slots, text):
        self.classified_intent = intent
        self.slots_extracted = slots
        self.agent_turn_text = text


async def mock_llm_fn(messages, node_name, asr_text):
    """A simulated LLM that provides the right slots to advance the graph."""
    if node_name == "opener":
        return MockStructuredAgentResponse("affirm", {}, "Hello")
    elif node_name == "identity_confirm":
        return MockStructuredAgentResponse("affirm", {"name_confirmed": True, "has_time": True}, "Great")
    elif node_name == "qualify":
        # Any primary slot works
        return MockStructuredAgentResponse("provide_value", {"monthly_income_inr": 50000, "monthly_revenue_inr": 50000}, "Okay")
    elif node_name == "qualify_followup":
        # Any followup slot works (we lowered req to 1)
        slots = {
            "loan_purpose": "medical",
            "gold_weight_grams": 10,
            "property_value_inr": 1000000,
            "vehicle_type": "car",
            "car_model": "SUV",
            "course_name": "BTech",
            "business_purpose": "working_capital",
            "monthly_spending_inr": 10000
        }
        return MockStructuredAgentResponse("provide_value", slots, "Got it")
    elif node_name == "consent":
        return MockStructuredAgentResponse("affirm", {"consent_given": True}, "Thanks")
    elif node_name == "next_step":
        return MockStructuredAgentResponse("affirm", {}, "Bye")
    elif node_name == "close":
        return MockStructuredAgentResponse("unclear", {}, "End")
    
    return MockStructuredAgentResponse("unclear", {}, "Unknown")


@pytest.mark.asyncio
@pytest.mark.parametrize("product", ALL_PRODUCTS)
async def test_full_call_completes(product):
    """Verify opener → close flow for every product without real LLM calls."""
    builder = PRODUCT_BUILDERS[product]
    app = builder(mock_llm_fn)
    
    config = {"configurable": {"thread_id": f"test_{product}"}}
    
    # Initialize state
    initial_state = {
        "call_id": f"test_{product}",
        "customer_id": "cust_123",
        "product": product,
        "agent_name": "Test Agent",
        "lender_name": "Test Bank",
        "customer_name": "Test Customer",
        "asr_text": "hello",
    }
    
    result_state = initial_state
    
    # Run the graph until the end, resuming after each interrupt
    while True:
        result_state = await app.ainvoke(result_state, config)
        if result_state["current_node"] == "close":
            break
        # Mock the pipeline injecting the next asr_text after an interrupt
        result_state["asr_text"] = "Yes I am interested"
        # We need to pass None to resume from the checkpoint
        result_state = None
        
    # The graph should successfully reach the close node
    # Since we can't easily assert the final state if it's interrupted inside close,
    # we just get the state from the checkpoint
    final_state = app.get_state(config).values
    assert final_state["current_node"] == "close"
    assert getattr(final_state["slots"], "outcome", None) == "qualified" or final_state["slots"].get("outcome") == "qualified"
