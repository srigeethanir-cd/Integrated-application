"""Frontend Artifact Generator — Generates React / TS / JS UI components for user stories."""

import logging
from typing import Any, Dict, Optional
# pyrefly: ignore [missing-import]
from app.utils.llm_client import LLMClient
# pyrefly: ignore [missing-import]
from agents.agent2_story_generator.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class FrontendGenerator:
    """Generates frontend React UI components."""

    def __init__(self, llm: Optional[LLMClient] = None) -> None:
        self.llm = llm or LLMClient()
        self.prompt_builder = PromptBuilder()

    def generate(
        self,
        story: Dict[str, Any],
        decision: Dict[str, Any],
        blueprint: Optional[Dict[str, Any]] = None,
        tech_stack: str = "React / JavaScript",
    ) -> str:
        """Generate frontend React component code.

        Returns string containing UI component code.
        """
        prompt = self.prompt_builder.build_generation_prompt(
            artifact_type="frontend",
            story=story,
            decision=decision,
            blueprint=blueprint,
            tech_stack=tech_stack,
        )

        try:
            if hasattr(self.llm, "generate") or hasattr(self.llm, "predict"):
                res = self.llm.generate(prompt)
                if isinstance(res, str) and len(res) > 20:
                    return self._clean_code(res)
        except Exception as e:
            logger.warning("LLM call failed for FrontendGenerator, falling back to template: %s", str(e))

        return self._generate_fallback(story, decision)

    @staticmethod
    def _clean_code(raw: str) -> str:
        if "```jsx" in raw:
            return raw.split("```jsx")[1].split("```")[0].strip()
        elif "```tsx" in raw:
            return raw.split("```tsx")[1].split("```")[0].strip()
        elif "```" in raw:
            return raw.split("```")[1].split("```")[0].strip()
        return raw.strip()

    @staticmethod
    def _generate_fallback(story: Dict[str, Any], decision: Dict[str, Any]) -> str:
        module = decision.get("module_name", "feature")
        comp = decision.get("component_name", "Feature")
        story_key = story.get("story_key") or story.get("key") or "US-001"
        story_title = story.get("title", "Feature Component")

        if module == "password_reset":
            return f'''import React, {{ useState }} from 'react';

export const ForgotPasswordComponent: React.FC = () => {{
  const [email, setEmail] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {{
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    setTimeout(() => {{
      setLoading(false);
      setIsSubmitted(true);
    }}, 600);
  }};

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-2xl shadow-sm border border-slate-200">
      <div className="mb-4">
        <span className="text-[10px] font-bold tracking-wider text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full uppercase">
          {story_key} • Security
        </span>
        <h2 className="text-xl font-bold text-slate-800 mt-2">{story_title}</h2>
        <p className="text-xs text-slate-500 mt-1">
          Enter your account email address to receive password recovery instructions.
        </p>
      </div>

      {{isSubmitted ? (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-center">
          <div className="text-emerald-700 font-semibold text-sm">✓ Recovery Email Sent!</div>
          <p className="text-xs text-emerald-600 mt-1">
            Check <b>{{email}}</b> for the password reset link. Token valid for 60 minutes.
          </p>
          <button
            onClick={{() => setIsSubmitted(false)}}
            className="mt-3 text-xs text-indigo-600 font-bold hover:underline"
          >
            Send another link
          </button>
        </div>
      ) : (
        <form onSubmit={{handleSubmit}} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Registered Email
            </label>
            <input
              type="email"
              required
              value={{email}}
              onChange={{(e) => setEmail(e.target.value)}}
              placeholder="user@example.com"
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <button
            type="submit"
            disabled={{loading}}
            className="w-full py-2.5 bg-indigo-600 text-white text-xs font-bold rounded-lg shadow-sm hover:bg-indigo-700 transition"
          >
            {{loading ? "Generating Reset Token..." : "Send Reset Link"}}
          </button>
        </form>
      )}}
    </div>
  );
}};

export default ForgotPasswordComponent;
'''
        elif module == "user_registration":
            return f'''import React, {{ useState }} from 'react';

export const UserRegistrationComponent: React.FC = () => {{
  const [formData, setFormData] = useState({{ username: '', email: '', password: '' }});
  const [success, setSuccess] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {{
    e.preventDefault();
    setSuccess(true);
  }};

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-2xl shadow-sm border border-slate-200">
      <span className="text-[10px] font-bold tracking-wider text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full uppercase">
        {story_key} • Authentication
      </span>
      <h2 className="text-xl font-bold text-slate-800 mt-2">{story_title}</h2>
      <p className="text-xs text-slate-500 mb-4">Create your secure user account.</p>

      {{success ? (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-700 text-xs font-semibold">
          ✓ Account created successfully for {{formData.username}}!
        </div>
      ) : (
        <form onSubmit={{handleSubmit}} className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-700">Username</label>
            <input
              type="text"
              required
              value={{formData.username}}
              onChange={{(e) => setFormData({{ ...formData, username: e.target.value }})}}
              className="w-full px-3 py-2 text-sm border rounded-lg focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700">Email Address</label>
            <input
              type="email"
              required
              value={{formData.email}}
              onChange={{(e) => setFormData({{ ...formData, email: e.target.value }})}}
              className="w-full px-3 py-2 text-sm border rounded-lg focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700">Password</label>
            <input
              type="password"
              required
              value={{formData.password}}
              onChange={{(e) => setFormData({{ ...formData, password: e.target.value }})}}
              className="w-full px-3 py-2 text-sm border rounded-lg focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <button type="submit" className="w-full py-2.5 bg-indigo-600 text-white text-xs font-bold rounded-lg hover:bg-indigo-700">
            Register Account
          </button>
        </form>
      )}}
    </div>
  );
}};

export default UserRegistrationComponent;
'''
        elif module == "user_login":
            return f'''import React, {{ useState }} from 'react';

export const UserLoginComponent: React.FC = () => {{
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {{
    e.preventDefault();
    setToken('jwt_session_' + Math.random().toString(36).substring(2));
  }};

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-2xl shadow-sm border border-slate-200">
      <span className="text-[10px] font-bold tracking-wider text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full uppercase">
        {story_key} • Login
      </span>
      <h2 className="text-xl font-bold text-slate-800 mt-2">{story_title}</h2>
      <p className="text-xs text-slate-500 mb-4">Sign in with your registered credentials.</p>

      {{token ? (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800">
          ✓ Logged in as <b>{{username}}</b> (Token issued)
        </div>
      ) : (
        <form onSubmit={{handleSubmit}} className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-700">Username / Email</label>
            <input
              type="text"
              required
              value={{username}}
              onChange={{(e) => setUsername(e.target.value)}}
              className="w-full px-3 py-2 text-sm border rounded-lg"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700">Password</label>
            <input
              type="password"
              required
              value={{password}}
              onChange={{(e) => setPassword(e.target.value)}}
              className="w-full px-3 py-2 text-sm border rounded-lg"
            />
          </div>
          <button type="submit" className="w-full py-2.5 bg-indigo-600 text-white text-xs font-bold rounded-lg hover:bg-indigo-700">
            Sign In
          </button>
        </form>
      )}}
    </div>
  );
}};

export default UserLoginComponent;
'''
        elif module == "dashboard_metrics":
            return f'''import React from 'react';

export const DashboardMetricsComponent: React.FC = () => {{
  const stats = [
    {{ label: 'Total Users', value: '1,284', change: '+12% this week', color: 'text-indigo-600' }},
    {{ label: 'Active Sessions', value: '94', change: 'Real-time', color: 'text-emerald-600' }},
    {{ label: 'System Uptime', value: '99.98%', change: 'All services green', color: 'text-blue-600' }},
  ];

  return (
    <div className="p-6 bg-white rounded-2xl shadow-sm border border-slate-200">
      <span className="text-[10px] font-bold tracking-wider text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full uppercase">
        {story_key} • Analytics
      </span>
      <h2 className="text-xl font-bold text-slate-800 mt-2">{story_title}</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        {{stats.map((s, i) => (
          <div key={{i}} className="p-4 bg-slate-50 border border-slate-100 rounded-xl">
            <div className="text-xs text-slate-500 font-medium">{{s.label}}</div>
            <div className={{"text-2xl font-bold mt-1 " + s.color}}>{{s.value}}</div>
            <div className="text-[10px] text-slate-400 mt-1">{{s.change}}</div>
          </div>
        ))}}
      </div>
    </div>
  );
}};

export default DashboardMetricsComponent;
'''
        else:
            fields = decision.get("fields", [])
            state_initializers = "\n".join(f"  const [{f.get('name')}, set{f.get('name').replace('_', ' ').title().replace(' ', '')}] = useState('');" for f in fields)
            
            form_elements = []
            for f in fields:
                fname = f.get('name')
                flabel = f.get('label')
                ftype = f.get('type', 'text')
                freq = "required" if f.get('required') else ""
                setter = f"set{fname.replace('_', ' ').title().replace(' ', '')}"
                
                if ftype == "textarea":
                    form_elements.append(f'''        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">{flabel}</label>
          <textarea
            value={{{fname}}}
            onChange={{(e) => {setter}(e.target.value)}}
            rows={{3}}
            placeholder="Enter {flabel}..."
            {freq}
            className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
          />
        </div>''')
                elif ftype == "select":
                    form_elements.append(f'''        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">{flabel}</label>
          <select
            value={{{fname}}}
            onChange={{(e) => {setter}(e.target.value)}}
            {freq}
            className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
          >
            <option value="">Select {flabel}...</option>
            <option value="option_1">Option 1 / Standard</option>
            <option value="option_2">Option 2 / High</option>
            <option value="option_3">Option 3 / Premium</option>
          </select>
        </div>''')
                else:
                    form_elements.append(f'''        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">{flabel}</label>
          <input
            type="{ftype}"
            value={{{fname}}}
            onChange={{(e) => {setter}(e.target.value)}}
            placeholder="Enter {flabel}..."
            {freq}
            className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
          />
        </div>''')
            
            form_inputs_jsx = "\n".join(form_elements) if form_elements else f'''        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Details</label>
          <input
            type="text"
            placeholder="Enter details..."
            className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg"
          />
        </div>'''

            return f'''import React, {{ useState }} from 'react';

export const {comp}Component: React.FC = () => {{
{state_initializers}
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {{
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    setTimeout(() => {{
      setLoading(false);
      setSuccessMsg("Successfully executed action for {story_title}.");
    }}, 500);
  }};

  return (
    <div className="p-6 bg-white rounded-2xl shadow-sm border border-slate-200 max-w-xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-bold tracking-wider text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full uppercase">
          {story_key} • {decision.get("module_name", "Feature")}
        </span>
        <span className="text-[10px] text-slate-400 font-mono">v1.0.0</span>
      </div>

      <div>
        <h2 className="text-xl font-bold text-slate-800">{story_title}</h2>
        <p className="text-xs text-slate-500 mt-1">{decision.get("description") or f"Direct execution component for {story_title}."}</p>
      </div>

      {{successMsg && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold rounded-xl flex items-center justify-between">
          <span>✓ {{successMsg}}</span>
          <button onClick={{() => setSuccessMsg(null)}} className="text-emerald-600 hover:text-emerald-800">×</button>
        </div>
      )}}

      {{errorMsg && (
        <div className="p-3.5 bg-red-50 border border-red-200 text-red-700 text-xs font-semibold rounded-xl">
          ⚠️ {{errorMsg}}
        </div>
      )}}

      <form onSubmit={{handleSubmit}} className="space-y-3.5 pt-2">
{form_inputs_jsx}

        <div className="flex gap-2 pt-2">
          <button
            type="submit"
            disabled={{loading}}
            className="flex-1 py-2.5 bg-indigo-600 text-white text-xs font-bold rounded-lg shadow-sm hover:bg-indigo-700 transition disabled:opacity-50"
          >
            {{loading ? 'Processing...' : '{decision.get("primary_action", "Submit").replace("_", " ").title()}'}}
          </button>
          <button
            type="button"
            onClick={{() => setSuccessMsg(null)}}
            className="px-4 py-2.5 bg-slate-100 text-slate-600 text-xs font-bold rounded-lg hover:bg-slate-200 transition"
          >
            Reset
          </button>
        </div>
      </form>
    </div>
  );
}};

export default {comp}Component;
'''
