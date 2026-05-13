"""Quick verification that all 10 product dialog graphs can be built and run."""
import asyncio
from typing import Any

# Product graph imports
from packages.dialog.dialog.personal_loan.graph import build_graph as build_personal_loan
from packages.dialog.dialog.home_loan.graph import build_graph as build_home_loan
from packages.dialog.dialog.credit_card.graph import build_graph as build_credit_card
from packages.dialog.dialog.education_loan.graph import build_graph as build_education_loan
from packages.dialog.dialog.gold_loan.graph import build_graph as build_gold_loan
from packages.dialog.dialog.four_wheeler.graph import build_graph as build_four_wheeler
from packages.dialog.dialog.commercial_vehicle.graph import build_graph as build_commercial_vehicle
from packages.dialog.dialog.lap_secured.graph import build_graph as build_lap_secured
from packages.dialog.dialog.msme_business.graph import build_graph as build_msme_business
from packages.dialog.dialog.unsecured_loan.graph import build_graph as build_unsecured_loan


PRODUCTS = {
    "personal_loan": build_personal_loan,
    "home_loan": build_home_loan,
    "credit_card": build_credit_card,
    "education_loan": build_education_loan,
    "gold_loan": build_gold_loan,
    "four_wheeler_loan": build_four_wheeler,
    "commercial_vehicle_loan": build_commercial_vehicle,
    "loan_against_property": build_lap_secured,
    "msme_business_loan": build_msme_business,
    "unsecured_loan": build_unsecured_loan,
}


async def mock_llm_fn(messages: list, node_name: str, asr_text: str) -> dict[str, Any]:
    """Mock LLM for testing - returns canned responses."""
    # Simulate different responses based on node
    responses = {
        "opener": {
            "text": "Namaste! Main Rahul bol raha hoon. Aapko personal loan ki information chahiye?",
            "continue": True,
        },
        "identity_confirm": {
            "text": "Theek hai. Kya aap apna full name bata sakte hain?",
            "slots": {},
            "continue": True,
        },
        "qualify": {
            "text": "Aapki monthly salary kitni hai?",
            "slots": {},
            "continue": True,
        },
        "qualify_followup": {
            "text": "Theek hai. Aapki loan amount kitni chahiye?",
            "slots": {"monthly_income": "50000"},
            "continue": True,
        },
        "consent": {
            "text": "Kya main aapki details record kar sakta hoon?",
            "slots": {},
            "continue": True,
        },
        "next_step": {
            "text": "Theek hai. Aapko confirmation SMS milega.",
            "continue": False,
        },
        "close": {
            "text": "Dhanyavaad! Aapka din shubh rahe.",
            "continue": False,
        },
    }

    return responses.get(node_name, {"text": "Okay", "continue": True})


async def verify_product(product_name: str, build_fn: Any) -> tuple[str, bool, str]:
    """Verify single product graph can build and run basic flow."""
    try:
        # Build graph
        app = build_fn(mock_llm_fn)

        # Initial state (all required DialogState fields)
        config = {"configurable": {"thread_id": f"test_{product_name}"}}
        initial_state = {
            "call_id": f"test_{product_name}",
            "customer_id": "test_customer_001",
            "product": product_name,
            "agent_name": "Rahul",
            "lender_name": "DemoBank",
            "customer_name": "Aman",
            "current_node": "opener",
            "asr_text": "",
            "history": [],
            "slots": {},
            "turn_index": 0,
        }

        # Run opener
        result = await app.ainvoke(initial_state, config)

        # Simulate customer response
        app.update_state(config, {"asr_text": "Yes, I need information"})
        result = await app.ainvoke(None, config)

        # Check we advanced past opener
        if result.get("current_node") not in ["opener", "__start__"]:
            return (product_name, True, f"[OK] Advanced to {result.get('current_node')}")
        else:
            return (product_name, False, "[FAIL] Stuck at opener")

    except Exception as e:
        return (product_name, False, f"[FAIL] Error: {str(e)[:100]}")


async def main():
    """Verify all 10 products."""
    print("=" * 60)
    print("SAARTHI Product Verification")
    print("=" * 60)
    print()

    results = []
    for product_name, build_fn in PRODUCTS.items():
        print(f"Testing {product_name}...", end=" ", flush=True)
        name, success, message = await verify_product(product_name, build_fn)
        results.append((name, success, message))
        print(message)

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    for name, success, message in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status:8} {name:30} {message}")

    print()
    print(f"Total: {passed}/{total} products verified")

    if passed == total:
        print("\n[OK] All products working!")
        return 0
    else:
        print(f"\n[FAIL] {total - passed} products failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
