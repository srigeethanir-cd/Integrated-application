"""
Integration & Unit Tests for Test Case Generator – Module 7.

Verifies:
1. POST /test_case/generate directly accepts StrategyPlanResponse output from POST /strategy/generate.
2. JSON dictionary output of StrategyPlanResponse is accepted without wrappers.
3. Structured execution test cases are generated covering Rendering, Form, State, Events, Services, Routing, Accessibility, and Edge cases.
4. FastAPI OpenAPI / Swagger schema displays StrategyPlanResponse directly as the request body.
"""

import tempfile
import shutil
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.project_analyzer.project_analyzer_service import ProjectAnalyzerService
from app.services.ir_generator.ir_generator_service import IRGeneratorService
from app.services.test_strategy.strategy_engine_service import StrategyEngine
from app.services.test_case_generator.test_case_generator import TestCaseGeneratorService
from app.models.strategy_models import StrategyPlanResponse
from app.models.test_case_models import TestCasePlanResponse


client = TestClient(app)


@pytest.fixture
def sample_react_project():
    """Create a temporary React project directory with a full component layout."""
    td = tempfile.mkdtemp()
    proj_dir = Path(td)

    # package.json
    (proj_dir / "package.json").write_text(
        '{"name": "test-app", "dependencies": {"react": "^18.2.0", "axios": "^1.0.0", "react-router-dom": "^6.0.0"}}'
    )

    # src/components/UserProfile.jsx
    src_dir = proj_dir / "src" / "components"
    src_dir.mkdir(parents=True, exist_ok=True)

    code = """
import React, { useState } from 'react';
import axios from 'axios';

export default function UserProfile({ userId, onUpdate }) {
    const [name, setName] = useState('');
    const [status, setStatus] = useState('idle');

    const handleSave = async (e) => {
        e.preventDefault();
        setStatus('saving');
        try {
            await axios.post(`/api/users/${userId}`, { name });
            setStatus('success');
            if (onUpdate) onUpdate(name);
        } catch (err) {
            setStatus('error');
        }
    };

    return (
        <form onSubmit={handleSave} className="user-profile-form">
            <h2>User Profile</h2>
            <input
                id="user-name"
                type="text"
                value={name}
                aria-label="User Name"
                onChange={(e) => setName(e.target.value)}
                required
            />
            <button type="submit" disabled={status === 'saving'}>
                Save
            </button>
            {status === 'saving' && <span>Saving...</span>}
            {status === 'error' && <span className="error">Failed to save</span>}
        </form>
    );
}
"""
    (src_dir / "UserProfile.jsx").write_text(code)

    yield str(proj_dir)
    shutil.rmtree(td, ignore_errors=True)


def test_test_case_generator_direct_strategy_plan(sample_react_project):
    """Verify TestCaseGeneratorService directly accepts StrategyPlanResponse object."""
    analyzer = ProjectAnalyzerService()
    analysis = analyzer.analyze(sample_react_project)

    ir_service = IRGeneratorService()
    ir = ir_service.generate_ir(analysis)

    engine = StrategyEngine()
    strategy_plan: StrategyPlanResponse = engine.generate_strategies(ir)

    tc_service = TestCaseGeneratorService()
    test_case_plan: TestCasePlanResponse = tc_service.generate_test_cases(strategy_plan)

    assert test_case_plan is not None
    assert test_case_plan.project_name == strategy_plan.project_name
    assert test_case_plan.total_test_cases > 0
    assert len(test_case_plan.test_cases) > 0

    # Verify structured attributes on test cases
    for tc in test_case_plan.test_cases:
        assert tc.id.startswith("TC-")
        assert tc.strategy_id
        assert tc.component == "UserProfile"
        assert tc.steps and len(tc.steps) == 4  # Arrange, Act, Assert, Cleanup
        assert tc.metadata is not None
        assert tc.metadata.locator is not None


def test_test_case_generate_api_endpoint(sample_react_project):
    """Verify POST /test_case/generate accepts StrategyPlanResponse JSON output directly."""
    analyzer = ProjectAnalyzerService()
    analysis = analyzer.analyze(sample_react_project)

    ir_service = IRGeneratorService()
    ir = ir_service.generate_ir(analysis)

    engine = StrategyEngine()
    strategy_plan: StrategyPlanResponse = engine.generate_strategies(ir)
    strat_json = strategy_plan.model_dump(mode="json")

    # Send strategy JSON directly to /test_case/generate without any wrapper
    response = client.post("/test_case/generate", json=strat_json)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

    data = response.json()
    assert data["project_name"] == strategy_plan.project_name
    assert data["total_test_cases"] > 0
    assert len(data["test_cases"]) > 0

    # Assert categories coverage
    categories = {tc["category"] for tc in data["test_cases"]}
    assert any("form" in c.lower() or "event" in c.lower() or "state" in c.lower() for c in categories)


def test_openapi_swagger_schema():
    """Verify OpenAPI schema displays StrategyPlanResponse as request body for POST /test_case/generate."""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    path_item = schema["paths"]["/test_case/generate"]["post"]
    request_body = path_item["requestBody"]

    assert request_body is not None
    content = request_body["content"]["application/json"]
    schema_ref = content["schema"]["$ref"]

    # Must reference StrategyPlanResponse directly
    assert "StrategyPlanResponse" in schema_ref
