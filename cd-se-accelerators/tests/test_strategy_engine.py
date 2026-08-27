"""
Unit and Integration tests for Test Strategy Engine strategy mapping (Module 5).
"""

import shutil
import tempfile
from pathlib import Path

import pytest
from app.models.analyzer_models import AnalyzerResponse
from app.models.ir_models import FrameworkAgnosticIR
from app.models.strategy_models import StrategyPlanResponse, TestStrategy
from app.services.project_analyzer.project_analyzer_service import ProjectAnalyzerService
from app.services.ir_generator.ir_generator_service import IRGeneratorService
from app.services.test_strategy.strategy_engine_service import StrategyEngine


@pytest.fixture
def temp_react_project():
    """Create a temporary React project directory for Strategy Engine testing."""
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


def test_strategy_generation_react(temp_react_project):
    # 1. Parse and generate IR
    analyzer = ProjectAnalyzerService()
    analysis_res: AnalyzerResponse = analyzer.analyze(str(temp_react_project))
    ir_service = IRGeneratorService()
    ir: FrameworkAgnosticIR = ir_service.generate_ir(analysis_res)
    
    # 2. Run Strategy Engine
    engine = StrategyEngine()
    plan: StrategyPlanResponse = engine.generate_strategies(ir)
    
    # 3. Assert strategy counts and categorization
    assert len(plan.strategies) >= 5
    assert plan.framework in ("React", "Next.js")
    
    # Assert presence of specific behavior-driven strategies
    init_strat = next(s for s in plan.strategies if s.id == "STRAT-LoginForm-REND-INIT")
    assert init_strat.category == "Component Initialization"
    assert init_strat.priority == "High"
    assert init_strat.risk == "High (10/10)"  # High risk due to API & hooks
    assert "without runtime exceptions" in init_strat.expected_outcome
    assert init_strat.behavior_reference is not None
    assert init_strat.component_id == "comp_src_components_LoginForm_jsx_LoginForm"
    
    # Form validation strategies
    success_form = next(s for s in plan.strategies if s.id == "STRAT-LoginForm-native-FORM-SUCCESS")
    assert success_form.category == "Form Validation Tests"
    assert "onSubmit" in success_form.description
    
    fail_form = next(s for s in plan.strategies if s.id == "STRAT-LoginForm-native-FORM-VALIDATION")
    assert fail_form.category == "Form Validation Tests"
    assert "validation rules" in fail_form.description
    
    # API Success and Failure strategies
    api_success = next(s for s in plan.strategies if s.id == "STRAT-LoginForm-API-SUCCESS-axios.post")
    assert api_success.category == "API/Service Interaction Tests"
    assert api_success.service_id == "svc_comp_src_components_LoginForm_jsx_LoginForm_axios.post"
    assert "axios.post" in api_success.description
    
    api_failure = next(s for s in plan.strategies if s.id == "STRAT-LoginForm-API-FAILURE-axios.post")
    assert api_failure.category == "Error Handling Tests"
    assert "network failures" in api_failure.description
    
    # Hook Lifecycle strategy
    hook_strat = next(s for s in plan.strategies if s.id == "STRAT-LoginForm-HOOKS-LIFECYCLE")
    assert hook_strat.category == "State Management Tests"
    assert "useState" in hook_strat.description or "useAuth" in hook_strat.description

    # Edge Case strategies
    xss_form = next(s for s in plan.strategies if s.id == "EC-STRAT-LoginForm-native-FORM-SUCCESS-INVALID-FORMAT")
    assert xss_form.category == "Form Validation Tests"
    assert "malformed" in xss_form.description.lower()

    timeout_api = next(s for s in plan.strategies if s.id == "EC-STRAT-LoginForm-API-ASYNC-axios.post-TIMEOUT")
    assert timeout_api.category == "Error Handling Tests"
    assert "timeout" in timeout_api.description.lower()

    rapid_evt = next(s for s in plan.strategies if s.id == "EC-STRAT-LoginForm-EVT-MOD-handleSubmit-RAPID-CLICK")
    assert rapid_evt.category == "Event Handling Tests"
    assert "rapid consecutive" in rapid_evt.description.lower() or "rapid click" in rapid_evt.description.lower()

    state_trans = next(s for s in plan.strategies if s.id == "EC-STRAT-LoginForm-STATE-TRANS-email-STATE-TRANSITION")
    assert state_trans.category == "State Management Tests"
    assert "state transition" in state_trans.description.lower()
