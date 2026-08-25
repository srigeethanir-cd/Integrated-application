"""Diagnostic: test memo, forwardRef, useReducer, Redux, routing, GraphQL."""
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
    '{"name":"t","dependencies":{"react":"^18.2.0","react-router-dom":"^6","react-redux":"^8","@apollo/client":"^3","zustand":"^4"}}'
)
src_dir = proj_dir / "src" / "components"
src_dir.mkdir(parents=True, exist_ok=True)

COUNTER_CODE = r"""
import React, { memo, forwardRef, useRef, useReducer, useEffect, useMemo } from 'react';
import { Link, useNavigate, Route } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { gql, useQuery } from '@apollo/client';

const QUERY = gql`query GetUser { user { id name } }`;

const reducer = (state, action) => {
    switch (action.type) {
        case 'INCREMENT': return { count: state.count + 1 };
        case 'DECREMENT': return { count: state.count - 1 };
        default: return state;
    }
};

export const Counter = memo(function Counter({ label, step = 1, onCountChange, className }) {
    const [state, dispatch] = useReducer(reducer, { count: 0 });
    const navigate = useNavigate();
    const reduxCount = useSelector(s => s.count);
    const { data, loading } = useQuery(QUERY);
    const timerRef = useRef(null);

    const doubled = useMemo(() => state.count * 2, [state.count]);

    useEffect(() => {
        timerRef.current = setTimeout(() => {}, 1000);
        return () => clearTimeout(timerRef.current);
    }, []);

    const handleIncrement = () => {
        dispatch({ type: 'INCREMENT' });
        if (onCountChange) onCountChange(state.count + step);
    };

    const handleNav = () => {
        navigate('/dashboard');
    };

    return (
        <div role="region" aria-label={label} className={className}>
            {loading && <span>Loading...</span>}
            <p>{state.count} / {doubled}</p>
            {data && data.user && <p>{data.user.name}</p>}
            <button onClick={handleIncrement} aria-label="Increment">Increment</button>
            <button onClick={handleNav}>Go to Dashboard</button>
            <Link to="/dashboard">Dashboard</Link>
            <Route path="/counter" component={Counter} />
            {state.count > 10 ? <span>High</span> : <span>Low</span>}
        </div>
    );
});

export const InputRef = forwardRef(function InputRef({ placeholder, label }, ref) {
    return (
        <label htmlFor="ref-input">
            {label}
            <input id="ref-input" ref={ref} placeholder={placeholder} aria-label={placeholder} required />
        </label>
    );
});
"""

ZUSTAND_CODE = r"""
import create from 'zustand';
import { useEffect } from 'react';
import fetch from 'node-fetch';

const useStore = create(set => ({
    count: 0,
    increment: () => set(s => ({ count: s.count + 1 })),
}));

export function ZustandComp({ title }) {
    const count = useStore(s => s.count);
    const increment = useStore(s => s.increment);

    useEffect(() => {
        fetch('/api/items')
            .then(r => r.json())
            .then(data => console.log(data))
            .catch(err => console.error(err));
    }, []);

    return (
        <div>
            <h1>{title}</h1>
            <p>{count}</p>
            <button onClick={increment}>Add</button>
        </div>
    );
}
"""

(src_dir / "Counter.jsx").write_text(COUNTER_CODE)
(src_dir / "ZustandComp.jsx").write_text(ZUSTAND_CODE)

try:
    svc = ProjectAnalyzerService()
    res = svc.analyze(str(proj_dir))

    print("All components:", [c.name for c in res.analysis.components])

    counter = next((c for c in res.analysis.components if c.name == "Counter"), None)
    input_ref = next((c for c in res.analysis.components if c.name == "InputRef"), None)
    zcomp = next((c for c in res.analysis.components if c.name == "ZustandComp"), None)

    if counter:
        cd = counter.model_dump()
        for sec in ["props", "state", "hooks", "routing_info", "conditional_rendering", "context_usage", "api_calls", "accessibility"]:
            print(f"\n=== COUNTER.{sec.upper()} ===")
            print(json.dumps(cd.get(sec), indent=2))
        print(f"\nCOUNTER type={cd['type']} complexity={cd['complexity_score']} risk={cd['risk_score']}")

    if input_ref:
        ifd = input_ref.model_dump()
        print("\n=== INPUTREF props ===", json.dumps(ifd["props"], indent=2))
        print("=== INPUTREF forms ===", json.dumps(ifd["forms"], indent=2))
        print("=== INPUTREF accessibility ===", json.dumps(ifd["accessibility"], indent=2))

    if zcomp:
        zd = zcomp.model_dump()
        print("\n=== ZUSTAND state ===", json.dumps(zd["state"], indent=2))
        print("=== ZUSTAND api_calls ===", json.dumps(zd["api_calls"], indent=2))
        print("=== ZUSTAND hooks ===", json.dumps(zd["hooks"], indent=2))
finally:
    shutil.rmtree(td, ignore_errors=True)
