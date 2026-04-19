"""Parametrized tests for all 10 product YAMLs and dialog packages."""
import pytest
import yaml
from pathlib import Path

PRODUCTS = [
    "personal_loan", "home_loan", "education_loan", "gold_loan", "credit_card",
    "unsecured_loan", "lap_secured", "commercial_vehicle", "four_wheeler", "msme_business"
]

YAML_DIR = Path(__file__).parent.parent / "products"


@pytest.mark.parametrize("product", PRODUCTS)
def test_yaml_exists(product):
    """Verify YAML file exists for each product."""
    yaml_file = YAML_DIR / f"{product}.yaml"
    assert yaml_file.exists(), f"{product}.yaml not found at {yaml_file}"


@pytest.mark.parametrize("product", PRODUCTS)
def test_yaml_loads(product):
    """Verify YAML parses without errors."""
    yaml_file = YAML_DIR / f"{product}.yaml"
    data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{product}.yaml did not parse to dict"


@pytest.mark.parametrize("product", PRODUCTS)
def test_yaml_schema(product):
    """Verify YAML has required structure."""
    yaml_file = YAML_DIR / f"{product}.yaml"
    data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))

    # Check top-level fields
    assert data.get("product") == product, f"Product ID mismatch in {product}.yaml"
    assert "version" in data, f"Missing version in {product}.yaml"
    assert "nodes" in data, f"Missing nodes in {product}.yaml"

    # Check required nodes
    required_nodes = ["opener", "identity_confirm", "qualify", "consent", "next_step", "close"]
    for node in required_nodes:
        assert node in data["nodes"], f"Missing node '{node}' in {product}.yaml"

    # Verify qualify has follow_up
    assert "follow_up" in data["nodes"]["qualify"], f"Missing follow_up in {product}.yaml qualify node"


@pytest.mark.parametrize("product", PRODUCTS)
def test_dialog_state_loads(product):
    """Verify DialogState class imports correctly."""
    module = __import__(f"dialog.{product}.state", fromlist=["DialogState"])
    assert hasattr(module, "DialogState"), f"DialogState not found in dialog.{product}.state"
    assert hasattr(module, "SlotSet"), f"SlotSet not found in dialog.{product}.state"


@pytest.mark.parametrize("product", PRODUCTS)
def test_dialog_state_default_product(product):
    """Verify DialogState has correct default product."""
    module = __import__(f"dialog.{product}.state", fromlist=["DialogState"])
    state = module.DialogState(
        call_id="test",
        customer_id="cust1",
        agent_name="Agent",
        lender_name="Bank",
        customer_name="Customer"
    )
    assert state.product == product, f"Default product mismatch: {state.product} != {product}"


@pytest.mark.parametrize("product", PRODUCTS)
def test_slotset_has_required_fields(product):
    """Verify SlotSet has name_confirmed, has_time, consent_given, outcome."""
    module = __import__(f"dialog.{product}.state", fromlist=["SlotSet"])
    slot_set = module.SlotSet()

    assert hasattr(slot_set, "name_confirmed"), f"Missing name_confirmed in {product} SlotSet"
    assert hasattr(slot_set, "has_time"), f"Missing has_time in {product} SlotSet"
    assert hasattr(slot_set, "consent_given"), f"Missing consent_given in {product} SlotSet"
    assert hasattr(slot_set, "outcome"), f"Missing outcome in {product} SlotSet"


@pytest.mark.parametrize("product", PRODUCTS)
def test_prompts_module_loads(product):
    """Verify prompts module loads and has required functions."""
    module = __import__(f"dialog.{product}.prompts", fromlist=["build_messages"])
    assert hasattr(module, "build_messages"), f"build_messages not found in dialog.{product}.prompts"
    assert hasattr(module, "get_fallback_text"), f"get_fallback_text not found in dialog.{product}.prompts"


@pytest.mark.parametrize("product", PRODUCTS)
def test_graph_module_loads(product):
    """Verify graph module loads and has build_graph function."""
    module = __import__(f"dialog.{product}.graph", fromlist=["build_graph"])
    assert hasattr(module, "build_graph"), f"build_graph not found in dialog.{product}.graph"
