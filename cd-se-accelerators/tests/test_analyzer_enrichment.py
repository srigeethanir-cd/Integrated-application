"""
Unit and Integration tests for Project Analyzer & Parser enrichment (Module 3).
"""

import shutil
import tempfile
from pathlib import Path

import pytest
from app.models.analyzer_models import (
    AnalyzerResponse,
    DependencyNode,
    ReactAnalysisResult,
    ReactComponentInfo,
    TestingMetadata,
)
from app.services.project_analyzer.project_analyzer_service import (
    ProjectAnalyzerService,
)


@pytest.fixture
def temp_project():
    """Create a temporary React project directory for analyzer testing."""
    td = tempfile.mkdtemp()
    proj_dir = Path(td)

    # package.json
    (proj_dir / "package.json").write_text(
        '{"name": "test-app", "dependencies": {"react": "^18.2.0", "axios": "^1.0.0"}}'
    )

    # src/components/LoginForm.jsx
    src_dir = proj_dir / "src" / "components"
    src_dir.mkdir(parents=True, exist_ok=True)

    login_form_code = """
import React, { useState } from 'react';
import axios from 'axios';
import { useAuth } from '../hooks/useAuth';

export default function LoginForm({ title = 'Login', onSubmitSuccess }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const { login } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const res = await axios.post('/api/login', { email, password });
            login(res.data.token);
            if (onSubmitSuccess) onSubmitSuccess();
        } catch (err) {
            setError('Login failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="login-form">
            <h2>{title}</h2>
            {error && <div className="error">{error}</div>}
            <input
                id="email-input"
                type="email"
                placeholder="Enter email"
                aria-label="Email Address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
            />
            <input
                id="password-input"
                type="password"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
            />
            <button type="submit" disabled={loading}>
                {loading ? 'Logging in...' : 'Submit'}
            </button>
        </form>
    );
}
"""
    (src_dir / "LoginForm.jsx").write_text(login_form_code)

    # src/components/StatCard.jsx
    stat_card_code = """
import React from 'react';

export function StatCard({ label, value }) {
    return (
        <div className="stat-card">
            <span>{label}</span>
            <h3>{value}</h3>
        </div>
    );
}
"""
    (src_dir / "StatCard.jsx").write_text(stat_card_code)

    yield proj_dir
    shutil.rmtree(td, ignore_errors=True)


def test_analyzer_enrichment_react(temp_project):
    service = ProjectAnalyzerService()
    res: AnalyzerResponse = service.analyze(str(temp_project))

    assert res.framework in ("React", "Next.js")
    assert isinstance(res.analysis, ReactAnalysisResult)

    analysis: ReactAnalysisResult = res.analysis
    assert len(analysis.components) >= 2

    # Verify component sorting and deduplication
    comp_names = [c.name for c in analysis.components]
    assert comp_names == sorted(comp_names)

    login_comp: ReactComponentInfo = next(
        c for c in analysis.components if c.name == "LoginForm"
    )

    # 1. Enriched Component Analysis
    assert login_comp.business_purpose == "User Authentication & Access Management"
    assert login_comp.complexity_score >= 5
    assert login_comp.risk_score >= 5
    assert login_comp.test_priority == "high"
    assert login_comp.confidence_score == 1.0
    assert len(login_comp.forms) > 0
    assert len(login_comp.forms[0].fields) >= 2

    # 2. Testing Metadata
    tm: TestingMetadata = login_comp.testing_metadata
    assert tm is not None
    assert "Forms" in tm.recommended_test_categories
    assert "API" in tm.recommended_test_categories
    assert len(tm.recommended_queries) > 0
    assert len(tm.edge_cases) > 0
    assert len(tm.negative_scenarios) > 0
    assert len(tm.suggested_mocks) > 0

    # 3. Dependency Node Categorization
    dep: DependencyNode = login_comp.dependency_graph
    assert dep is not None
    assert "axios" in dep.imports_external_libraries
    assert "useAuth" in dep.imports_hooks

    # 4. Coverage Analysis & Gaps
    assert "LoginForm" in analysis.uncovered_components
    assert len(analysis.coverage_gaps) > 0


def test_path_normalization_posix(temp_project):
    service = ProjectAnalyzerService()
    res: AnalyzerResponse = service.analyze(str(temp_project))

    analysis: ReactAnalysisResult = res.analysis
    for comp in analysis.components:
        assert "\\" not in comp.file_path
