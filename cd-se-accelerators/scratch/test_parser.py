import sys, tempfile, os, json
sys.path.insert(0, ".")
from app.services.project_analyzer.react_parser import ReactParser

d = tempfile.mkdtemp()
code = """
import React, { useState } from 'react';

export function LoginForm({ onLoginSuccess }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    const handleEmailChange = (e) => {
        setEmail(e.target.value);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
    };

    return (
        <form onSubmit={handleSubmit}>
            <input value={email} onChange={handleEmailChange} />
            <button type="submit">Submit</button>
        </form>
    );
}
"""
with open(os.path.join(d, "LoginForm.jsx"), "w", encoding="utf-8") as f:
    f.write(code)

parser = ReactParser()
res = parser.parse(d)
print(json.dumps(res, indent=2))
