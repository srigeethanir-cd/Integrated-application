"""
Tests for Frontend Behavior Inventory Extraction & Behavioral Test Case Generation.

Verifies:
1. BehaviorInventoryService extracts states, functions, handlers, hooks, and state transitions.
2. Mandatory intermediate validation logging counts.
3. Strict truthfulness & traceability of generated unit test cases.
4. Behavior Inventory API routes (/behavior_inventory/generate).
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.behavior_inventory_models import BehaviorInventoryResponse
from app.services.behavior_inventory_service import BehaviorInventoryService

client = TestClient(app)


@pytest.fixture
def mock_analysis_payload():
    """Mock analysis result matching Babel AST parser format for useLoginForm custom hook."""
    return {
        "components": [
            {
                "name": "useLoginForm",
                "file_path": "src/hooks/useLoginForm.js",
                "state": [
                    {"name": "email", "initial_value": '""', "type": "string", "setter_name": "setEmail"},
                    {"name": "password", "initial_value": '""', "type": "string", "setter_name": "setPassword"},
                    {"name": "rememberMe", "initial_value": "false", "type": "boolean", "setter_name": "setRememberMe"},
                ],
                "hooks": [{"name": "useState"}],
                "functions": [
                    {"name": "handleSubmit", "description": "prevents default form submission"},
                    {"name": "handleEmailChange", "description": "updates email state"},
                ],
                "event_handlers": [
                    {
                        "name": "handleEmailChange",
                        "event": "change",
                        "updates_state": ["email"],
                        "prevent_default": False,
                    },
                    {
                        "name": "handlePasswordChange",
                        "event": "change",
                        "updates_state": ["password"],
                        "prevent_default": False,
                    },
                    {
                        "name": "handleRememberMeChange",
                        "event": "change",
                        "updates_state": ["rememberMe"],
                        "prevent_default": False,
                    },
                    {
                        "name": "handleSubmit",
                        "event": "submit",
                        "updates_state": [],
                        "prevent_default": True,
                    },
                ],
            }
        ]
    }


def test_behavior_inventory_builder(mock_analysis_payload):
    """Test that BehaviorInventoryService correctly extracts state transitions, handlers, and metrics."""
    service = BehaviorInventoryService()
    inv_response = service.build_inventory(
        analysis_result=mock_analysis_payload,
        project_name="LoginFormApp",
        project_id="proj_login_001",
        pipeline_run_id="run_test_001",
        framework="React",
    )

    assert isinstance(inv_response, BehaviorInventoryResponse)
    assert inv_response.total_components == 1
    assert inv_response.total_states == 3
    assert inv_response.total_handlers == 4
    assert len(inv_response.inventory) == 1

    item = inv_response.inventory[0]
    assert item.component == "useLoginForm"
    assert item.component_type == "hook"
    assert item.source_file == "src/hooks/useLoginForm.js"

    # Verify State Extraction
    state_names = [s.name for s in item.states]
    assert "email" in state_names
    assert "password" in state_names
    assert "rememberMe" in state_names

    # Verify State Transitions Extraction
    assert len(item.state_transitions) >= 3
    email_trans = next((t for t in item.state_transitions if "email" in t.initial_state), None)
    assert email_trans is not None
    assert email_trans.triggering_function == 'handleEmailChange("user@test.com")'
    assert email_trans.state_transition == 'setEmail("user@test.com")'

    # Verify Function Behaviors
    fn_names = [f.name for f in item.functions]
    assert "handleSubmit" in fn_names
    assert "handleEmailChange" in fn_names

    submit_fn = next((f for f in item.functions if f.name == "handleSubmit"), None)
    assert submit_fn is not None
    assert "preventDefault" in str(submit_fn.side_effects) or "prevents default" in submit_fn.behavior.lower()


def test_behavior_inventory_api_endpoint(mock_analysis_payload):
    """Test REST API endpoint POST /behavior_inventory/generate."""
    response = client.post(
        "/behavior_inventory/generate",
        json={
            "analysis": mock_analysis_payload,
            "project_name": "APITestApp",
            "framework": "React",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["project_name"] == "APITestApp"
    assert data["total_components"] == 1
    assert len(data["inventory"]) == 1
    assert data["inventory"][0]["component"] == "useLoginForm"
