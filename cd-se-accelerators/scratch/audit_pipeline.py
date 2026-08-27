import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from app.models.pipeline_models import PipelineRunRequest
from app.services.pipeline_orchestrator_service import PipelineOrchestratorService

# Project 1: Multi-component app (LoginForm, UserProfile, BrandHeader, TodoList, CartItem)
PROJ1_COMPONENTS = {
    "LoginForm.jsx": """
import React, { useState } from 'react';

export function LoginForm({ onLoginSuccess }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleEmailChange = (e) => setEmail(e.target.value);
    const handlePasswordChange = (e) => setPassword(e.target.value);

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
        <form onSubmit={handleSubmit}>
            <input id="email" value={email} onChange={handleEmailChange} />
            <input id="password" value={password} onChange={handlePasswordChange} />
            <button type="submit" disabled={isLoading}>Submit</button>
        </form>
    );
}
""",
    "UserProfile.jsx": """
import React, { useState, useEffect } from 'react';

export function UserProfile({ userId, onLogout }) {
    const [profile, setProfile] = useState(null);
    const [isEditing, setIsEditing] = useState(false);

    useEffect(() => {
        fetch(`/api/users/${userId}`)
            .then(res => res.json())
            .then(data => setProfile(data));
    }, [userId]);

    const handleToggleEdit = () => setIsEditing(!isEditing);
    const handleSave = async (e) => {
        e.preventDefault();
        await fetch(`/api/users/${userId}`, { method: 'PUT', body: JSON.stringify(profile) });
        setIsEditing(false);
    };

    if (!profile) return <div>Loading...</div>;

    return (
        <div>
            <h2>{profile.name}</h2>
            <button onClick={handleToggleEdit}>{isEditing ? 'Cancel' : 'Edit'}</button>
            {isEditing && (
                <form onSubmit={handleSave}>
                    <button type="submit">Save</button>
                </form>
            )}
            <button onClick={onLogout}>Logout</button>
        </div>
    );
}
""",
    "TodoList.jsx": """
import React, { useState } from 'react';

export function TodoList() {
    const [items, setItems] = useState([]);
    const [text, setText] = useState('');

    const handleTextChange = (e) => setText(e.target.value);
    const handleAddItem = (e) => {
        e.preventDefault();
        if (!text.trim()) return;
        setItems([...items, { id: Date.now(), text, completed: false }]);
        setText('');
    };

    const handleToggleItem = (id) => {
        setItems(items.map(it => it.id === id ? { ...it, completed: !it.completed } : it));
    };

    const handleDeleteItem = (id) => {
        setItems(items.filter(it => it.id !== id));
    };

    return (
        <div>
            <form onSubmit={handleAddItem}>
                <input value={text} onChange={handleTextChange} placeholder="Add item" />
                <button type="submit">Add</button>
            </form>
            <ul>
                {items.map(item => (
                    <li key={item.id}>
                        <span onClick={() => handleToggleItem(item.id)}>{item.text}</span>
                        <button onClick={() => handleDeleteItem(item.id)}>Delete</button>
                    </li>
                ))}
            </ul>
        </div>
    );
}
"""
}

# Project 2: Counter & Theme Switcher (Single small app)
PROJ2_COMPONENTS = {
    "Counter.jsx": """
import React, { useState } from 'react';

export function Counter({ initialCount = 0 }) {
    const [count, setCount] = useState(initialCount);

    const handleIncrement = () => setCount(count + 1);
    const handleDecrement = () => setCount(count - 1);
    const handleReset = () => setCount(0);

    return (
        <div>
            <span data-testid="count">{count}</span>
            <button onClick={handleIncrement}>+</button>
            <button onClick={handleDecrement}>-</button>
            <button onClick={handleReset}>Reset</button>
        </div>
    );
}
"""
}

async def run_audit(name, components_dict):
    tmp_dir = tempfile.mkdtemp(prefix=f"audit_{name}_")
    src_dir = Path(tmp_dir) / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    pkg_code = '{"name": "' + name + '", "dependencies": {"react": "^18.2.0"}}'
    (Path(tmp_dir) / "package.json").write_text(pkg_code, encoding="utf-8")

    for fname, code in components_dict.items():
        (src_dir / fname).write_text(code, encoding="utf-8")

    orchestrator = PipelineOrchestratorService()
    req = PipelineRunRequest(project_path=tmp_dir, run_until="test_case_generator")
    res = await orchestrator.run_pipeline(req)

    print(f"\n==================== AUDIT REPORT: {name} ====================")
    print(f"Status: {res.status}")
    if res.outputs.analysis:
        comps = res.outputs.analysis.get("components", [])
        print(f"Babel Components: {len(comps)} -> {[c.get('name') for c in comps]}")
    if res.outputs.strategy_plan:
        strats = res.outputs.strategy_plan.get("strategies", [])
        print(f"Strategies: {len(strats)}")
    if res.outputs.edge_case_plan:
        ecs = res.outputs.edge_case_plan.get("edge_cases", [])
        print(f"Edge Cases: {len(ecs)}")
    if res.outputs.test_case_plan:
        tc_plan = res.outputs.test_case_plan
        tcs = tc_plan.get("test_cases", [])
        cov = tc_plan.get("coverage_summary", {})
        print(f"Raw Generated Cases in Plan: {len(tcs)}")
        print(f"Coverage Summary: {cov}")
        for idx, tc in enumerate(tcs):
            print(f"  {idx+1}. [{tc.get('component')}] [{tc.get('target_function')}] {tc.get('title')}")

    shutil.rmtree(tmp_dir, ignore_errors=True)

async def main():
    await run_audit("Project1_MultiComponent", PROJ1_COMPONENTS)
    await run_audit("Project2_CounterOnly", PROJ2_COMPONENTS)

if __name__ == "__main__":
    asyncio.run(main())
