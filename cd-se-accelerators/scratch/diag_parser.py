"""Diagnostic: run the parser against a fixture and print all fields."""
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.project_analyzer.project_analyzer_service import ProjectAnalyzerService

td = tempfile.mkdtemp()
proj_dir = Path(td)
(proj_dir / "package.json").write_text(
    '{"name":"test-app","dependencies":{"react":"^18.2.0","axios":"^1.0.0"}}'
)
src_dir = proj_dir / "src" / "components"
src_dir.mkdir(parents=True, exist_ok=True)

LOGIN_CODE = r"""
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

MEMO_CODE = r"""
import React, { memo, forwardRef, useRef, useReducer } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';

const reducer = (state, action) => {
    switch (action.type) {
        case 'INCREMENT': return { count: state.count + 1 };
        default: return state;
    }
};

export const Counter = memo(function Counter({ label, step = 1, onCountChange }) {
    const [state, dispatch] = useReducer(reducer, { count: 0 });
    const navigate = useNavigate();
    const count = useSelector(s => s.count);

    const handleIncrement = () => {
        dispatch({ type: 'INCREMENT' });
        if (onCountChange) onCountChange(state.count + step);
    };

    return (
        <div role="region" aria-label={label}>
            <p>{state.count}</p>
            <button onClick={handleIncrement}>Increment</button>
            <Link to="/dashboard">Dashboard</Link>
            {state.count > 10 ? <span>High</span> : <span>Low</span>}
        </div>
    );
});

export const InputRef = forwardRef(function InputRef({ placeholder }, ref) {
    return <input ref={ref} placeholder={placeholder} aria-label={placeholder} />;
});
"""

(src_dir / "LoginForm.jsx").write_text(LOGIN_CODE)
(src_dir / "Counter.jsx").write_text(MEMO_CODE)

try:
    svc = ProjectAnalyzerService()
    res = svc.analyze(str(proj_dir))
    lf = next(c for c in res.analysis.components if c.name == "LoginForm")
    data = lf.model_dump()

    sections = [
        "props", "state", "hooks", "forms", "api_calls",
        "event_handlers", "conditional_rendering", "routing_info",
        "accessibility", "context_usage", "functions",
    ]
    for sec in sections:
        print(f"\n=== {sec.upper()} ===")
        print(json.dumps(data.get(sec), indent=2))

    print(f"\n=== SCORES: complexity={data['complexity_score']} risk={data['risk_score']} priority={data['test_priority']} ===")
    print(f"\n=== JSX_ELEMENTS ({len(data['jsx_elements'])}) ===")
    for el in data["jsx_elements"]:
        print(json.dumps(el, indent=2))

    # Check Counter too
    counter = next((c for c in res.analysis.components if c.name == "Counter"), None)
    if counter:
        cd = counter.model_dump()
        print("\n\n=== COUNTER: state ===")
        print(json.dumps(cd["state"], indent=2))
        print("=== COUNTER: routing_info ===")
        print(json.dumps(cd["routing_info"], indent=2))
        print("=== COUNTER: conditional_rendering ===")
        print(json.dumps(cd["conditional_rendering"], indent=2))

    print("\n\nAll components found:", [c.name for c in res.analysis.components])
finally:
    shutil.rmtree(td, ignore_errors=True)
