import React, { useState } from 'react';

export const UserLoginComponent: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setToken('jwt_session_' + Math.random().toString(36).substring(2));
  };

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-2xl shadow-sm border border-slate-200">
      <span className="text-[10px] font-bold tracking-wider text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full uppercase">
        US006 • Login
      </span>
      <h2 className="text-xl font-bold text-slate-800 mt-2">Social Login</h2>
      <p className="text-xs text-slate-500 mb-4">Sign in with your registered credentials.</p>

      {token ? (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800">
          ✓ Logged in as <b>{username}</b> (Token issued)
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-700">Username / Email</label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 text-sm border rounded-lg"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 text-sm border rounded-lg"
            />
          </div>
          <button type="submit" className="w-full py-2.5 bg-indigo-600 text-white text-xs font-bold rounded-lg hover:bg-indigo-700">
            Sign In
          </button>
        </form>
      )}
    </div>
  );
};

export default UserLoginComponent;
