"""
Integration & Unit Tests for Test Writer – Module 8.

Verifies:
1. POST /test_writer/generate directly accepts TestCasePlanResponse output from POST /test_case/generate.
2. JSON dictionary output of TestCasePlanResponse is accepted without wrappers.
3. React test file and test_manifest.json are generated and written to disk.
4. FastAPI OpenAPI / Swagger schema displays TestCasePlanResponse directly as the request body.
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
from app.services.test_writer.test_writer_service import TestWriterService
from app.models.strategy_models import StrategyPlanResponse
from app.models.test_case_models import TestCasePlanResponse
from app.models.test_writer_models import TestWriterResponse


client = TestClient(app)


@pytest.fixture
def sample_react_project():
    """Create a temporary React project directory with a full component layout."""
    td = tempfile.mkdtemp()
    proj_dir = Path(td)

    # package.json
    (proj_dir / "package.json").write_text(
        '{"name": "test-app", "dependencies": {"react": "^18.2.0", "axios": "^1.0.0"}}'
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


def test_test_writer_direct_test_case_plan(sample_react_project):
    """Verify TestWriterService directly accepts TestCasePlanResponse object."""
    analyzer = ProjectAnalyzerService()
    analysis = analyzer.analyze(sample_react_project)

    ir_service = IRGeneratorService()
    ir = ir_service.generate_ir(analysis)

    engine = StrategyEngine()
    strategy_plan: StrategyPlanResponse = engine.generate_strategies(ir)

    tc_service = TestCaseGeneratorService()
    test_case_plan: TestCasePlanResponse = tc_service.generate_test_cases(strategy_plan)

    tw_service = TestWriterService()
    res: TestWriterResponse = tw_service.generate_test_suite(test_case_plan, sample_react_project)

    assert res is not None
    assert res.total_files > 0
    assert len(res.generated_files) > 0
    assert res.manifest_path and Path(res.manifest_path).exists()


def test_test_writer_generate_api_endpoint(sample_react_project):
    """Verify POST /test_writer/generate accepts TestCasePlanResponse JSON output directly."""
    analyzer = ProjectAnalyzerService()
    analysis = analyzer.analyze(sample_react_project)

    ir_service = IRGeneratorService()
    ir = ir_service.generate_ir(analysis)

    engine = StrategyEngine()
    strategy_plan: StrategyPlanResponse = engine.generate_strategies(ir)

    tc_service = TestCaseGeneratorService()
    test_case_plan: TestCasePlanResponse = tc_service.generate_test_cases(strategy_plan)
    tc_json = test_case_plan.model_dump(mode="json")

    # Send test_case_plan JSON directly to /test_writer/generate without any wrapper
    response = client.post(
        f"/test_writer/generate?output_workspace_dir={sample_react_project}",
        json=tc_json
    )
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

    data = response.json()
    assert data["total_files"] > 0
    assert len(data["generated_files"]) > 0
    assert data["manifest_path"]


def test_test_writer_openapi_swagger_schema():
    """Verify OpenAPI schema displays TestCasePlanResponse as request body for POST /test_writer/generate."""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    path_item = schema["paths"]["/test_writer/generate"]["post"]
    request_body = path_item["requestBody"]

    assert request_body is not None
    content = request_body["content"]["application/json"]
    schema_ref = content["schema"]["$ref"]

    # Must reference TestCasePlanResponse directly
    assert "TestCasePlanResponse" in schema_ref
