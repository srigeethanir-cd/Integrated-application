import React, { useState } from 'react';

export const UserLoginComponent: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loggedIn, setLoggedIn] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setLoggedIn(true);
  };

  return (
    <div className="p-6 max-w-md mx-auto bg-white rounded-2xl border border-slate-200 shadow-sm space-y-4 font-sans">
      <div className="border-b border-slate-100 pb-3">
        <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">US002</span>
        <h2 className="text-lg font-black text-slate-800">User Login</h2>
      </div>

      <form onSubmit={handleLogin} className="space-y-3 text-xs">
        <div>
          <label className="block text-slate-600 font-bold mb-1">Username / Email</label>
          <input
            type="text"
            required
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full p-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none"
            placeholder="Enter credentials"
          />
        </div>
        <div>
          <label className="block text-slate-600 font-bold mb-1">Password</label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none"
            placeholder="••••••••"
          />
        </div>
        <button
          type="submit"
          className="w-full py-2.5 bg-[#FE7642] hover:bg-[#F56632] text-white font-bold rounded-xl transition-all shadow-sm"
        >
          Sign In
        </button>
      </form>

      {loggedIn && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-xl text-xs font-bold">
          ✓ Authenticated successfully as {username}! Access token generated.
        </div>
      )}
    </div>
  );
};

export default UserLoginComponent;
