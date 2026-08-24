"""Frontend Generator synthesizing production-ready React TypeScript components, layouts, and styles."""

import logging
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from agents.agent0_wireframe.screen_detector import DetectedScreen
from agents.agent0_wireframe.wireframe_analyzer import VisualUISpec

logger = logging.getLogger(__name__)


class GeneratedFile(BaseModel):
    """Model representing a scaffolded frontend file."""

    path: str = Field(description="Relative filepath under frontend project root (e.g. src/pages/DashboardPage.tsx)")
    content: str = Field(description="File source code content")


class FrontendGenerator:
    """Generates React TSX components, layout wrappers, CSS styles, and frontend project code structures."""

    def generate_main_layout(self, nav_data: Dict[str, Any], visual_spec: VisualUISpec) -> str:
        """Generate MainLayout.tsx wrapper component."""
        bg_color = visual_spec.color_palette[0] if visual_spec.color_palette else "#0f172a"
        return f"""import React, {{ useState }} from 'react';
import {{ Outlet, Link, useLocation }} from 'react-router-dom';

export const MainLayout: React.FC = () => {{
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const menuItems = {nav_data.get('sidebar_menu', [])};

  return (
    <div className="flex h-screen bg-slate-900 text-slate-100 font-sans">
      {{/* Sidebar */}}
      <aside className="{{`w-64 bg-slate-800 border-r border-slate-700 transition-all ${{sidebarOpen ? 'block' : 'hidden'}} md:block`}}">
        <div className="p-4 flex items-center justify-between border-b border-slate-700">
          <h1 className="text-xl font-bold text-blue-400">AI BA Accelerator</h1>
        </div>
        <nav className="p-4 space-y-2">
          {{menuItems.map((item: any) => (
            <Link
              key={{item.id}}
              to={{item.path}}
              className={{`flex items-center px-4 py-2 rounded-lg text-sm font-medium ${{
                location.pathname === item.path ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-700'
              }}`}}
            >
              <span>{{item.label}}</span>
            </Link>
          ))}}
        </nav>
      </aside>

      {{/* Main Content Area */}}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-slate-800 border-b border-slate-700 flex items-center justify-between px-6">
          <button onClick={{() => setSidebarOpen(!sidebarOpen)}} className="text-slate-300 md:hidden">
            Menu
          </button>
          <div className="text-sm text-slate-400">Environment: Production</div>
        </header>
        <main className="flex-1 overflow-y-auto p-6 bg-slate-950">
          <Outlet />
        </main>
      </div>
    </div>
  );
}};

export default MainLayout;
"""

    def generate_page_component(self, screen: DetectedScreen) -> str:
        """Generate React TSX code for a detected page screen."""
        if screen.screen_type == "login":
            return f"""import React, {{ useState }} from 'react';

export const {screen.component_name}: React.FC = () => {{
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e: React.FormEvent) => {{
    e.preventDefault();
    console.log('Login submitted:', {{ email, password }});
  }};

  return (
    <div className="max-w-md mx-auto my-12 bg-slate-800 p-8 rounded-xl shadow-xl border border-slate-700">
      <h2 className="text-2xl font-bold text-center text-white mb-6">{screen.name}</h2>
      <form onSubmit={{handleSubmit}} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">Email Address</label>
          <input
            type="email"
            value={{email}}
            onChange={{(e) => setEmail(e.target.value)}}
            className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
            placeholder="user@example.com"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">Password</label>
          <input
            type="password"
            value={{password}}
            onChange={{(e) => setPassword(e.target.value)}}
            className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
            placeholder="••••••••"
            required
          />
        </div>
        <button
          type="submit"
          className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-semibold transition"
        >
          Sign In
        </button>
      </form>
    </div>
  );
}};

export default {screen.component_name};
"""
        elif screen.screen_type == "table":
            return f"""import React from 'react';

export const {screen.component_name}: React.FC = () => {{
  const sampleData = [
    {{ id: '1', name: 'Item Alpha', status: 'Active', updated: '2026-07-21' }},
    {{ id: '2', name: 'Item Beta', status: 'Pending', updated: '2026-07-20' }},
    {{ id: '3', name: 'Item Gamma', status: 'Completed', updated: '2026-07-19' }},
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">{screen.name}</h2>
        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm">
          + Add New
        </button>
      </div>

      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-900 text-slate-400 uppercase text-xs">
            <tr>
              <th className="px-6 py-3">ID</th>
              <th className="px-6 py-3">Name</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3">Last Updated</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {{sampleData.map((row) => (
              <tr key={{row.id}} className="hover:bg-slate-700/50">
                <td className="px-6 py-4 font-mono text-slate-400">{{row.id}}</td>
                <td className="px-6 py-4 font-medium text-white">{{row.name}}</td>
                <td className="px-6 py-4">
                  <span className="px-2 py-1 text-xs rounded bg-blue-900/50 text-blue-300 border border-blue-700">
                    {{row.status}}
                  </span>
                </td>
                <td className="px-6 py-4 text-slate-400">{{row.updated}}</td>
              </tr>
            ))}}
          </tbody>
        </table>
      </div>
    </div>
  );
}};

export default {screen.component_name};
"""
        else:
            return f"""import React from 'react';

export const {screen.component_name}: React.FC = () => {{
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">{screen.name}</h2>
      <p className="text-slate-400">{screen.description}</p>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
          <div className="text-slate-400 text-sm">Total Metrics</div>
          <div className="text-3xl font-bold text-white mt-2">1,248</div>
        </div>
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
          <div className="text-slate-400 text-sm">Active Sessions</div>
          <div className="text-3xl font-bold text-blue-400 mt-2">94.2%</div>
        </div>
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
          <div className="text-slate-400 text-sm">System Health</div>
          <div className="text-3xl font-bold text-emerald-400 mt-2">Operational</div>
        </div>
      </div>
    </div>
  );
}};

export default {screen.component_name};
"""

    def generate_all_files(
        self,
        screens: List[DetectedScreen],
        nav_data: Dict[str, Any],
        routes_code: str,
        visual_spec: VisualUISpec,
    ) -> List[GeneratedFile]:
        """Generate full list of frontend React TSX files."""
        files: List[GeneratedFile] = []

        # Routes & Layout
        files.append(GeneratedFile(path="src/routes/AppRoutes.tsx", content=routes_code))
        files.append(
            GeneratedFile(
                path="src/layouts/MainLayout.tsx",
                content=self.generate_main_layout(nav_data, visual_spec),
            )
        )

        # Page components
        for screen in screens:
            files.append(
                GeneratedFile(
                    path=f"src/pages/{screen.component_name}.tsx",
                    content=self.generate_page_component(screen),
                )
            )

        return files
