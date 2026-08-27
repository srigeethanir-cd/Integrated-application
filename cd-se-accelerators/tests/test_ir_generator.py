"""
Unit and Integration tests for IR Generator mapping (Module 4).
"""

import shutil
import tempfile
from pathlib import Path

import pytest
from app.models.analyzer_models import AnalyzerResponse
from app.models.ir_models import ComponentIR, FrameworkAgnosticIR
from app.services.project_analyzer.project_analyzer_service import ProjectAnalyzerService
from app.services.ir_generator.ir_generator_service import IRGeneratorService


@pytest.fixture
def temp_react_project():
    """Create a temporary React project directory for IR generator testing."""
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
    import React, { useState, useMemo } from 'react';
    import axios from 'axios';
    import { useAuth } from '../hooks/useAuth';

    export default function LoginForm({ title = 'Login', onSubmitSuccess }) {
        const [email, setEmail] = useState('');
        const [password, setPassword] = useState('');
        const [loading, setLoading] = useState(false);
        const [error, setError] = useState(null);

        const { login } = useAuth();
        
        const isReady = useMemo(() => email && password, [email, password]);

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

    yield proj_dir
    shutil.rmtree(td, ignore_errors=True)


def test_ir_generation_react(temp_react_project):
    # 1. Parse project
    analyzer = ProjectAnalyzerService()
    res: AnalyzerResponse = analyzer.analyze(str(temp_react_project))
    
    # 2. Map to IR
    ir_service = IRGeneratorService()
    ir: FrameworkAgnosticIR = ir_service.generate_ir(res)
    
    # 3. Assert on IR structure
    assert ir.framework in ("React", "Next.js")
    assert len(ir.components) >= 1
    
    lf: ComponentIR = next(c for c in ir.components if c.name == "LoginForm")
    
    # Check component ID normalization (contains normalized path + name)
    assert lf.id == "comp_src_components_LoginForm_jsx_LoginForm"
    
    # Check dynamic risk scoring and reasons
    assert lf.risk_score >= 5.0
    assert lf.risk_analysis is not None
    assert lf.risk_analysis.score >= 5
    assert len(lf.risk_analysis.risk_reasons) > 0
    
    # Check accessibility detail mapping
    assert lf.accessibility_detail is not None
    assert "Email Address" in lf.accessibility_detail.labels
    
    # Check form control field mapping
    assert len(lf.forms) == 1
    form = lf.forms[0]
    assert form.library == "native"
    assert form.submit_handler == "handleSubmit"
    assert len(form.controls) == 2
    
    email_field = next(c for c in form.controls if c.name == "email-input")
    assert email_field.type == "email"
    assert email_field.is_controlled is True
    assert email_field.is_required is True
    assert "required" in email_field.validation_rules
    assert "email" in email_field.validation_rules
    
    # Check render conditions mapping (uses correctly spelled conditional_rendering)
    assert len(lf.render_conditions) >= 2
    err_cond = next(c for c in lf.render_conditions if c.condition == "error")
    assert "div" in err_cond.affected_ui
    
    # Check testability mapping
    assert lf.testability is not None
    assert "getByLabelText" in lf.testability.recommended_rtl_queries
    assert "axios.post" in lf.testability.mock_dependencies
    
    # Check data flow mapping
    assert lf.data_flow is not None
    assert "useMemo" in lf.data_flow.memoized_values
    
    # Check top-level collections mapping (no data loss)
    assert len(ir.forms) == 1
