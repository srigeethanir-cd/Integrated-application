"""
Automated Test Suite for Frontend Context Extraction Engine (FCE).

Verifies:
1. React component detection, useState, initial values, setters.
2. Function extraction, parameters, reads, writes.
3. Event handler & JSX event extraction.
4. Conditional branch extraction.
5. API/service call detection.
6. Child component extraction.
7. State transition extraction.
8. Context completeness validation report metrics.
9. Project & cache isolation.
10. Safe fallback handling (FCE errors do not crash pipeline).
11. REST API endpoint POST /frontend_context/extract.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.frontend_context.context_engine import FrontendContextEngine
from app.services.frontend_context.file_analyzer import clear_context_cache, compute_file_hash, get_cached_context, set_cached_context
from app.services.frontend_context.models import FrontendContextResponse, SingleComponentFrontendContext

client = TestClient(app)


@pytest.fixture
def mock_react_analysis():
    """Mock analysis output for useLoginForm custom hook and LoginForm component."""
    return {
        "components": [
            {
                "name": "useLoginForm",
                "file_path": "src/hooks/useLoginForm.js",
                "state": [
                    {"name": "email", "initial_value": '""', "type": "string", "setter": "setEmail"},
                    {"name": "password", "initial_value": '""', "type": "string", "setter": "setPassword"},
                    {"name": "rememberMe", "initial_value": "false", "type": "boolean", "setter": "setRememberMe"},
                ],
                "hooks": [{"name": "useState"}],
                "functions": [
                    {
                        "name": "handleEmailChange",
                        "params": ["event"],
                        "reads": ["event.target.value"],
                        "writes": ["email"],
                        "behavior": "updates email state",
                    },
                    {
                        "name": "handleSubmit",
                        "params": ["event"],
                        "reads": ["email", "password"],
                        "writes": [],
                        "behavior": "prevents default form submission and submits credentials",
                    },
                ],
                "event_handlers": [
                    {"name": "handleEmailChange", "event": "change", "element": "input"},
                    {"name": "handleSubmit", "event": "submit", "element": "form", "prevent_default": True},
                ],
                "api_calls": [
                    {
                        "function_name": "fetch",
                        "endpoint": "/api/login",
                        "http_method": "POST",
                        "is_async": True,
                        "has_error_handling": True,
                    }
                ],
                "children": ["BrandHeader", "SubmitButton"],
            }
        ]
    }


def test_fce_extraction_engine(mock_react_analysis):
    """Verify ground-truth static context extraction, state setters, functions, and state transitions."""
    engine = FrontendContextEngine()
    res = engine.extract_context(
        analysis_result=mock_react_analysis,
        project_name="LoginFormApp",
        project_id="proj_fce_001",
        pipeline_run_id="run_fce_001",
        framework="React",
    )

    assert isinstance(res, FrontendContextResponse)
    assert res.project_name == "LoginFormApp"
    assert res.project_id == "proj_fce_001"
    assert len(res.contexts) == 1

    ctx = res.contexts[0]
    assert ctx.component_name == "useLoginForm"
    assert ctx.source_file == "src/hooks/useLoginForm.js"

    # 1. State Extraction & Setters
    state_map = {s.name: s for s in ctx.states}
    assert "email" in state_map
    assert state_map["email"].setter == "setEmail"
    assert state_map["password"].setter == "setPassword"
    assert state_map["rememberMe"].setter == "setRememberMe"

    # 2. Function Extraction
    fn_names = [f.name for f in ctx.functions]
    assert "handleEmailChange" in fn_names
    assert "handleSubmit" in fn_names

    email_fn = next(f for f in ctx.functions if f.name == "handleEmailChange")
    assert "event" in email_fn.parameters
    assert "email" in email_fn.writes

    # 3. Event Handlers
    ev_names = [e.name for e in ctx.events]
    assert "change" in ev_names or "handleEmailChange" in [e.handler for e in ctx.events]

    # 4. API Calls & Children
    assert len(ctx.api_calls) == 1
    assert ctx.api_calls[0].http_method == "POST"

    child_names = [c.name for c in ctx.child_components]
    assert "BrandHeader" in child_names or "SubmitButton" in child_names

    # 5. Behaviors & State Transitions
    assert len(ctx.behaviors) >= 2
    assert len(ctx.state_transitions) >= 3

    email_trans = next(t for t in ctx.state_transitions if "email" in t.initial_state)
    assert email_trans.state_transition == 'setEmail("user@test.com")'

    # 6. Completeness Report
    rep = res.completeness_report
    assert rep.components_discovered == 1
    assert rep.components_analyzed == 1
    assert rep.functions_discovered >= 2
    assert rep.states_discovered == 3


def test_fce_cache_isolation():
    """Verify context caching and cross-project isolation."""
    clear_context_cache()

    ctx1 = SingleComponentFrontendContext(
        project_id="proj_A",
        component_id="comp_1",
        component_name="Header",
        source_file="src/Header.jsx",
    )
    set_cached_context("proj_A", "src/Header.jsx", "hash123", ctx1)

    cached_a = get_cached_context("proj_A", "src/Header.jsx", "hash123")
    assert cached_a is not None
    assert cached_a.component_name == "Header"

    # Isolated lookup for different project
    cached_b = get_cached_context("proj_B", "src/Header.jsx", "hash123")
    assert cached_b is None


def test_fce_safe_fallback():
    """Verify that FCE handles malformed component data without crashing."""
    engine = FrontendContextEngine()
    malformed_analysis = {"components": [{"invalid_key": None}]}

    res = engine.extract_context(
        analysis_result=malformed_analysis,
        project_name="FallbackApp",
        project_id="proj_fallback",
        framework="React",
    )

    assert isinstance(res, FrontendContextResponse)
    assert res.project_name == "FallbackApp"
    assert len(res.contexts) == 1
    assert res.contexts[0].component_name == "Component"


def test_fce_api_endpoint(mock_react_analysis):
    """Verify REST API endpoint POST /frontend_context/extract."""
    response = client.post(
        "/frontend_context/extract",
        json={
            "analysis": mock_react_analysis,
            "project_name": "APIApp",
            "framework": "React",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["project_name"] == "APIApp"
    assert len(data["contexts"]) == 1
    assert data["contexts"][0]["component_name"] == "useLoginForm"


def test_behavior_context_bridge(mock_react_analysis):
    """Verify BehaviorContextBridge converts extracted facts into explicit behavior test scenarios."""
    from app.services.frontend_context.behavior_context_bridge import BehaviorContextBridge
    engine = FrontendContextEngine()
    fce_res = engine.extract_context(
        analysis_result=mock_react_analysis,
        project_name="BridgeTestApp",
        project_id="proj_bridge",
        framework="React",
    )

    bridge = BehaviorContextBridge()
    scenarios = bridge.generate_scenarios(fce_res)

    assert len(scenarios) >= 2
    
    # 1. Check handleEmailChange state handler scenario
    email_sc = next((s for s in scenarios if s["function"] == "handleEmailChange"), None)
    assert email_sc is not None
    assert "updates email state" in email_sc["behavior"]
    assert "handleEmailChange" in email_sc["test_title"]
    assert email_sc["category"] == "State"
    assert len(email_sc["steps"]) == 4

    # 2. Check handleSubmit form submission scenario
    submit_sc = next((s for s in scenarios if s["function"] == "handleSubmit"), None)
    assert submit_sc is not None
    assert "prevents default" in submit_sc["behavior"]
    assert submit_sc["category"] == "Forms"


def test_behavior_driven_test_generation_integration(mock_react_analysis):
    """Verify TestCaseGeneratorService consumes FrontendContext to generate behavior-driven test cases."""
    from app.services.frontend_context.behavior_context_bridge import BehaviorContextBridge
    from app.services.test_case_generator.test_case_generator import TestCaseGeneratorService
    from app.models.strategy_models import StrategyPlanResponse, TestStrategy
    from app.models.edge_case_models import EdgeCasePlanResponse, EdgeCaseScenario
    from app.models.ir_models import ComponentIR, FrameworkAgnosticIR
    from app.utils.ir_cache import cache_ir

    engine = FrontendContextEngine()
    fce_res = engine.extract_context(
        analysis_result=mock_react_analysis,
        project_name="IntegrationApp",
        project_id="proj_integration",
        pipeline_run_id="run_integration",
        framework="React",
    )

    # Setup mock IR
    ir = FrameworkAgnosticIR(
        project_id="proj_integration",
        pipeline_run_id="run_integration",
        framework="React",
        components=[
            ComponentIR(
                name="useLoginForm",
                type="functional",
                file_path="src/hooks/useLoginForm.js",
                functions=[{"name": "handleEmailChange"}, {"name": "handleSubmit"}],
            )
        ]
    )
    cache_ir(ir, key="run_integration")

    base_strat = TestStrategy(
        id="STRAT-001",
        component_id="comp_useLoginForm",
        target_component="useLoginForm",
        category="State",
        priority="High",
        test_objective="Verify state behavior in useLoginForm",
        description="Verify state management",
    )
    base_ec = EdgeCaseScenario(
        id="EC-STRAT-001-01",
        strategy_id="STRAT-001",
        category="State",
        priority="High",
        title="Valid state transition",
        description="State updates correctly",
        expected_behavior="State updates correctly",
    )

    strat_plan = StrategyPlanResponse(
        project_name="IntegrationApp",
        project_id="proj_integration",
        pipeline_run_id="run_integration",
        framework="React",
        strategies=[base_strat],
    )
    ec_plan = EdgeCasePlanResponse(
        project_name="IntegrationApp",
        project_id="proj_integration",
        pipeline_run_id="run_integration",
        framework="React",
        edge_cases=[base_ec],
    )

    gen = TestCaseGeneratorService()
    tc_plan = gen.generate_test_cases(
        strategy_plan=strat_plan,
        edge_case_plan=ec_plan,
        frontend_context=fce_res,
    )

    assert tc_plan.total_test_cases >= 2
    # Verify titles are behavior-driven, not generic
    titles = [tc.title for tc in tc_plan.test_cases]
    assert any("handleEmailChange" in t for t in titles)
    assert any("handleSubmit" in t for t in titles)
    assert not any("executes handler logic safely" in t for t in titles)

