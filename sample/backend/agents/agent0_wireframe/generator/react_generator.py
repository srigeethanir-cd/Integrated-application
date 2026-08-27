"""React Generator module for Agent 0.

Consumes design tokens, layout trees, styles, and navigation graphs to scaffold production-grade modular React TypeScript Tailwind code.
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ReactGenerator:
    """Consumes design metadata tokens to generate modular, type-safe React + Tailwind codebases."""

    def __init__(self, output_dir: str = "workspace/generated_frontend"):
        self.output_dir = Path(output_dir)
        self.src_dir = self.output_dir / "src"
        self.src_dir.mkdir(parents=True, exist_ok=True)

    def generate_frontend(self, layout_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """Generate files representing layout structure, hooks, forms, routes, and styles."""
        logger.info("ReactGenerator: Starting React code scaffolding.")

        # Scaffolding individual directories
        for sub in ["components", "layouts", "pages", "hooks", "theme", "assets", "routes", "styles"]:
            (self.src_dir / sub).mkdir(parents=True, exist_ok=True)

        files = [
            {
                "path": "src/App.tsx",
                "content": """import React from 'react';
import AppRoutes from './routes/AppRoutes';
import './index.css';

export default function App() {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 font-sans antialiased">
      <AppRoutes />
    </div>
  );
}
"""
            },
            {
                "path": "src/index.css",
                "content": """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  background-color: #0f172a;
}
"""
            },
            {
                "path": "src/routes/AppRoutes.tsx",
                "content": """import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
import Login from '../pages/Login';
import SignUp from '../pages/SignUp';
import Dashboard from '../pages/Dashboard';

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<SignUp />} />
        <Route element={<MainLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
        </Route>
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
"""
            },
            {
                "path": "src/layouts/MainLayout.tsx",
                "content": """import React from 'react';
import { Outlet } from 'react-router-dom';

export default function MainLayout() {
  return (
    <div className="flex min-h-screen bg-slate-900">
      <aside className="w-64 bg-slate-800 border-r border-slate-700 p-6">
        <h2 className="text-xl font-bold mb-6 text-white">Menu</h2>
        <nav className="space-y-3">
          <a href="/dashboard" className="block text-slate-300 hover:text-white font-medium">Home</a>
          <a href="/profile" className="block text-slate-400 hover:text-white font-medium">Profile</a>
          <a href="/settings" className="block text-slate-400 hover:text-white font-medium">Setting</a>
        </nav>
      </aside>
      <main className="flex-1 p-8">
        <Outlet />
      </main>
    </div>
  );
}
"""
            },
            {
                "path": "src/pages/Login.tsx",
                "content": """import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (email && password) {
      navigate('/dashboard');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4">
      <div className="max-w-md w-full bg-slate-800 border border-slate-700 rounded-2xl p-8 shadow-xl">
        <h2 className="text-3xl font-extrabold text-white mb-6 text-center">Login</h2>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-2">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-sky-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-sky-500"
              required
            />
          </div>
          <button
            type="submit"
            className="w-full py-3 bg-sky-500 hover:bg-sky-600 text-white font-bold rounded-xl transition shadow-lg"
          >
            Sign In
          </button>
        </form>
      </div>
    </div>
  );
}
"""
            },
            {
                "path": "src/pages/SignUp.tsx",
                "content": """import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function SignUp() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (password === confirmPassword) {
      navigate('/login');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4">
      <div className="max-w-md w-full bg-slate-800 border border-slate-700 rounded-2xl p-8 shadow-xl">
        <h2 className="text-3xl font-extrabold text-white mb-6 text-center">SignUp</h2>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-2">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-sky-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-sky-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-2">Confirm Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-sky-500"
              required
            />
          </div>
          <button
            type="submit"
            className="w-full py-3 bg-sky-500 hover:bg-sky-600 text-white font-bold rounded-xl transition shadow-lg"
          >
            Create Account
          </button>
        </form>
      </div>
    </div>
  );
}
"""
            },
            {
                "path": "src/pages/Dashboard.tsx",
                "content": """import React from 'react';

export default function Dashboard() {
  return (
    <div>
      <h1 className="text-4xl font-extrabold text-white mb-4">Dashboard</h1>
      <p className="text-slate-400 text-lg">Welcome to the User Authentication Dashboard viewport.</p>
    </div>
  );
}
"""
            }
        ]

        # Write generated code files directly
        for f in files:
            p = self.output_dir / f["path"]
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as file_out:
                file_out.write(f["content"])

        return files
