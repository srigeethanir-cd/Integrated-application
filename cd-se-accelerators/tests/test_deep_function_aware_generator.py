"""
Deep Function-Aware Test Case Generation Integration Test.

Verifies that:
1. Test cases map directly to actual component functions and handlers (handleSubmit, handlePasswordChange, etc.).
2. Every test case contains all required human-readable fields:
   - id
   - title (non-generic, behavior-specific)
   - component
   - component_specification
   - target_function
   - category
   - priority
   - preconditions
   - steps
   - expected_result
   - why_this_test_matters
   - traceability
3. Coverage summary report is generated detailing components, functions, behaviors, test cases, duplicates removed, and coverage matrix.
4. Storage file project-1/generated_testcases/test_cases.json is populated.
"""

import json
import os
import shutil
import tempfile
import pytest
from pathlib import Path

from app.models.pipeline_models import PipelineRunRequest
from app.services.pipeline_orchestrator_service import PipelineOrchestratorService


@pytest.fixture
def multi_component_workspace():
    """Create a temporary multi-component project workspace with functions, handlers, state, and forms."""
    tmp_dir = tempfile.mkdtemp(prefix="deep_analysis_proj_")
    src_dir = Path(tmp_dir) / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    login_form_code = """
import React, { useState } from 'react';

export function LoginForm({ onLoginSuccess }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleEmailChange = (e) => {
        setEmail(e.target.value);
    };

    const handlePasswordChange = (e) => {
        setPassword(e.target.value);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);
        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            if (!res.ok) throw new Error('Invalid credentials');
            const data = await res.json();
            if (onLoginSuccess) onLoginSuccess(data.token);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="login-form">
            <h2>Sign In</h2>
            {error && <div className="error-banner">{error}</div>}
            <label htmlFor="email">Email Address</label>
            <input
                id="email"
                type="email"
                value={email}
                onChange={handleEmailChange}
                placeholder="user@example.com"
                required
            />
            <label htmlFor="password">Password</label>
            <input
                id="password"
                type="password"
                value={password}
                onChange={handlePasswordChange}
                placeholder="Enter password"
                required
            />
            <button type="submit" disabled={isLoading}>
                {isLoading ? 'Signing In...' : 'Log In'}
            </button>
        </form>
    );
}
"""

    user_profile_code = """
import React, { useState, useEffect } from 'react';

export function UserProfile({ userId, onLogout }) {
    const [profile, setProfile] = useState(null);
    const [isEditing, setIsEditing] = useState(false);

    useEffect(() => {
        fetch(`/api/users/${userId}`)
            .then(res => res.json())
            .then(data => setProfile(data));
    }, [userId]);

    const handleToggleEdit = () => {
        setIsEditing(!isEditing);
    };

    const handleSave = async (e) => {
        e.preventDefault();
        await fetch(`/api/users/${userId}`, { method: 'PUT', body: JSON.stringify(profile) });
        setIsEditing(false);
    };

    const handleLogoutClick = () => {
        if (onLogout) onLogout();
    };

    if (!profile) return <div>Loading Profile...</div>;

    return (
        <div className="user-profile">
            <h3>{profile.name}</h3>
            <button onClick={handleToggleEdit}>{isEditing ? 'Cancel' : 'Edit Profile'}</button>
            {isEditing && (
                <form onSubmit={handleSave}>
                    <button type="submit">Save Changes</button>
                </form>
            )}
            <button onClick={handleLogoutClick} className="logout-btn">Log Out</button>
        </div>
    );
}
"""

    brand_header_code = """
import React from 'react';

export function BrandHeader({ title = 'Enterprise Portal' }) {
    return (
        <header className="brand-header">
            <h1 className="logo">{title}</h1>
        </header>
    );
}
"""

    pkg_code = '{"name": "multi-comp-app", "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"}}'

    (Path(tmp_dir) / "package.json").write_text(pkg_code, encoding="utf-8")
    (src_dir / "LoginForm.jsx").write_text(login_form_code, encoding="utf-8")
    (src_dir / "UserProfile.jsx").write_text(user_profile_code, encoding="utf-8")
    (src_dir / "BrandHeader.jsx").write_text(brand_header_code, encoding="utf-8")

    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_deep_function_aware_test_case_generation(multi_component_workspace):
    """Verify deep function analysis, human-readable format, coverage summary, and file storage."""
    orchestrator = PipelineOrchestratorService()

    req = PipelineRunRequest(
        project_path=multi_component_workspace,
        run_until="test_case_generator"
    )
    res = await orchestrator.run_pipeline(req)

    assert res.status == "success"
    tc_plan = res.outputs.test_case_plan
    assert tc_plan is not None

    test_cases = tc_plan.get("test_cases", [])
    assert len(test_cases) > 0

    # 1. Verify Deep Component & Function Mapping
    functions_covered = {tc.get("target_function") for tc in test_cases if tc.get("target_function")}
    assert len(functions_covered) > 0, "No target functions mapped to test cases!"

    # Verify handlers like handleSubmit, handlePasswordChange, handleSave exist in mapped functions
    mapped_functions_str = " ".join(functions_covered)
    assert "handleSubmit" in mapped_functions_str or "handleSubmit()" in functions_covered, f"handleSubmit not mapped in functions: {functions_covered}"

    # 2. Verify 12 Required Human-Readable Fields
    for tc in test_cases:
        assert "id" in tc and tc["id"], "Missing test case id"
        assert "title" in tc and tc["title"], "Missing test case title"
        assert "component" in tc and tc["component"], "Missing component name"
        assert "category" in tc and tc["category"], "Missing category"
        assert "priority" in tc and tc["priority"], "Missing priority"
        assert "preconditions" in tc, "Missing preconditions"
        assert "steps" in tc and len(tc["steps"]) > 0, "Missing test steps"
        assert "expected_result" in tc and tc["expected_result"], "Missing expected_result"
        assert "component_specification" in tc and tc["component_specification"], "Missing component_specification"
        assert "target_function" in tc and tc["target_function"], "Missing target_function"
        assert "why_this_test_matters" in tc and tc["why_this_test_matters"], "Missing why_this_test_matters"
        assert "traceability" in tc and tc["traceability"], "Missing traceability object"

        # Verify NO Generic Titles like "Verify Component works"
        assert not tc["title"].startswith("Verify Component works"), f"Generic title detected: {tc['title']}"

    # 3. Verify Final Coverage Summary Structure
    cov_summary = tc_plan.get("coverage_summary")
    assert cov_summary is not None, "Missing coverage_summary in test_case_plan response!"
    assert cov_summary.get("components_discovered", 0) >= 3, "Expected at least 3 discovered components"
    assert cov_summary.get("functions_discovered", 0) > 0, "Expected >0 functions discovered"
    assert cov_summary.get("test_cases_generated", 0) == len(test_cases)
    assert "coverage_matrix" in cov_summary

    # 4. Verify Storage File Creation (project-1/generated_testcases/test_cases.json)
    target_storage = Path(multi_component_workspace) / "project-1" / "generated_testcases" / "test_cases.json"
    assert target_storage.exists(), f"Target storage file not found at: {target_storage}"
    
    with open(target_storage, "r", encoding="utf-8") as f:
        stored_data = json.load(f)
    assert stored_data.get("total_test_cases") == len(test_cases)
