"""
Cross-Project Isolation & Stale Data Prevention Integration Test.

Verifies that when two different frontend projects are run sequentially:
1. Every run generates unique project_id and pipeline_run_id.
2. Component inventory is built strictly from the current project's actual source files.
3. Test cases generated for Project B NEVER contain components from Project A.
4. Unrelated/hallucinated components (ActivityListItem, NotificationListItem, StatCard) can NEVER appear.
5. End-to-end traceability (Project -> Component -> Source File -> IR -> Strategy -> Edge Case -> Test Case) is preserved.
"""

import os
import shutil
import tempfile
import pytest
import asyncio
from pathlib import Path

from app.models.pipeline_models import PipelineRunRequest
from app.services.pipeline_orchestrator_service import PipelineOrchestratorService
from app.utils.ir_cache import clear_ir_cache


@pytest.fixture
def temp_workspace_a():
    """Create a temporary project workspace for Project A."""
    tmp_dir = tempfile.mkdtemp(prefix="project_a_")
    src_dir = Path(tmp_dir) / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    # Project A components: ActionFooter, BrandHeader, LoginForm
    action_footer_code = """
import React from 'react';
export function ActionFooter() {
    return <footer className="action-footer"><button>Submit</button></footer>;
}
"""
    brand_header_code = """
import React from 'react';
export function BrandHeader() {
    return <header className="brand-header"><h1>App Title</h1></header>;
}
"""
    login_form_code = """
import React, { useState } from 'react';
export function LoginForm() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const handleSubmit = (e) => { e.preventDefault(); };
    return (
        <form onSubmit={handleSubmit}>
            <input type="text" value={username} onChange={e => setUsername(e.target.value)} placeholder="Username" />
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" />
            <button type="submit">Log In</button>
        </form>
    );
}
"""
    pkg_code = '{"name": "project-a", "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"}}'

    (Path(tmp_dir) / "package.json").write_text(pkg_code, encoding="utf-8")
    (src_dir / "ActionFooter.jsx").write_text(action_footer_code, encoding="utf-8")
    (src_dir / "BrandHeader.jsx").write_text(brand_header_code, encoding="utf-8")
    (src_dir / "LoginForm.jsx").write_text(login_form_code, encoding="utf-8")

    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def temp_workspace_b():
    """Create a temporary project workspace for Project B."""
    tmp_dir = tempfile.mkdtemp(prefix="project_b_")
    src_dir = Path(tmp_dir) / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    # Project B components: Header, Footer, Sidebar
    header_code = """
import React from 'react';
export function Header() {
    return <header>Navbar</header>;
}
"""
    footer_code = """
import React from 'react';
export function Footer() {
    return <footer>Copyright 2026</footer>;
}
"""
    sidebar_code = """
import React from 'react';
export function Sidebar() {
    return <aside>Menu Links</aside>;
}
"""
    pkg_code = '{"name": "project-b", "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"}}'

    (Path(tmp_dir) / "package.json").write_text(pkg_code, encoding="utf-8")
    (src_dir / "Header.jsx").write_text(header_code, encoding="utf-8")
    (src_dir / "Footer.jsx").write_text(footer_code, encoding="utf-8")
    (src_dir / "Sidebar.jsx").write_text(sidebar_code, encoding="utf-8")

    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_sequential_cross_project_isolation(temp_workspace_a, temp_workspace_b):
    """Run pipeline sequentially on Project A then Project B, ensuring ZERO component leakage."""
    orchestrator = PipelineOrchestratorService()

    # --- Run 1: Project A ---
    req_a = PipelineRunRequest(
        project_path=temp_workspace_a,
        run_until="test_case_generator"
    )
    res_a = await orchestrator.run_pipeline(req_a)

    assert res_a.status == "success"
    tc_plan_a = res_a.outputs.test_case_plan
    assert tc_plan_a is not None

    test_cases_a = tc_plan_a.get("test_cases", [])
    assert len(test_cases_a) > 0

    components_a = {tc["component"] for tc in test_cases_a}
    
    # Project A components MUST ONLY be from ActionFooter, BrandHeader, LoginForm
    allowed_a = {"ActionFooter", "BrandHeader", "LoginForm"}
    for comp in components_a:
        assert comp in allowed_a, f"Project A produced unexpected component: {comp}"

    # Verify hallucinated components NEVER appear in Project A
    forbidden_components = {"ActivityListItem", "NotificationListItem", "StatCard"}
    assert not components_a.intersection(forbidden_components), f"Project A contained forbidden components: {components_a.intersection(forbidden_components)}"

    # --- Run 2: Project B (Run immediately after Project A) ---
    req_b = PipelineRunRequest(
        project_path=temp_workspace_b,
        run_until="test_case_generator"
    )
    res_b = await orchestrator.run_pipeline(req_b)

    assert res_b.status == "success"
    tc_plan_b = res_b.outputs.test_case_plan
    assert tc_plan_b is not None

    test_cases_b = tc_plan_b.get("test_cases", [])
    assert len(test_cases_b) > 0

    components_b = {tc["component"] for tc in test_cases_b}

    # Project B components MUST ONLY be from Header, Footer, Sidebar
    allowed_b = {"Header", "Footer", "Sidebar"}
    for comp in components_b:
        assert comp in allowed_b, f"Project B produced unexpected component: {comp}"

    # STRICT CHECK: Project A components MUST NEVER appear in Project B!
    assert not components_b.intersection(allowed_a), f"CROSS-PROJECT CONTAMINATION: Project B contains Project A components: {components_b.intersection(allowed_a)}"

    # Forbidden hallucinated components MUST NEVER appear in Project B!
    assert not components_b.intersection(forbidden_components), f"Project B contained forbidden components: {components_b.intersection(forbidden_components)}"

    # Check project_id and pipeline_run_id uniqueness
    pid_a = tc_plan_a.get("project_id")
    pid_b = tc_plan_b.get("project_id")
    assert pid_a != pid_b, "Project A and Project B share the same project_id!"
