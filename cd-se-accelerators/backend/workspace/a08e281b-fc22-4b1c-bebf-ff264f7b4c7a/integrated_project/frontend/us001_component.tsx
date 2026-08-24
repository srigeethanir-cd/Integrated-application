import React, { useState } from 'react';

export const UserRegistrationComponent: React.FC = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div className="p-6 max-w-md mx-auto bg-white rounded-2xl border border-slate-200 shadow-sm space-y-4 font-sans">
      <div className="border-b border-slate-100 pb-3">
        <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">US001</span>
        <h2 className="text-lg font-black text-slate-800">User Registration</h2>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3 text-xs">
        <div>
          <label className="block text-slate-600 font-bold mb-1">Username</label>
          <input
            type="text"
            required
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full p-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none"
            placeholder="johndoe"
          />
        </div>
        <div>
          <label className="block text-slate-600 font-bold mb-1">Email Address</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full p-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none"
            placeholder="john@example.com"
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
          className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl transition-all shadow-sm"
        >
          Create Account
        </button>
      </form>

      {submitted && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-xl text-xs font-bold">
          ✓ Account registration submitted successfully for {username}!
        </div>
      )}
    </div>
  );
};

export default UserRegistrationComponent;
