import React, { useState } from 'react';

export const ForgotPasswordComponent: React.FC = () => {
  const [email, setEmail] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setIsSubmitted(true);
    }, 600);
  };

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-2xl shadow-sm border border-slate-200">
      <div className="mb-4">
        <span className="text-[10px] font-bold tracking-wider text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full uppercase">
          US003 • Security
        </span>
        <h2 className="text-xl font-bold text-slate-800 mt-2">Forgot Password</h2>
        <p className="text-xs text-slate-500 mt-1">
          Enter your account email address to receive password recovery instructions.
        </p>
      </div>

      {isSubmitted ? (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-center">
          <div className="text-emerald-700 font-semibold text-sm">✓ Recovery Email Sent!</div>
          <p className="text-xs text-emerald-600 mt-1">
            Check <b>{email}</b> for the password reset link. Token valid for 60 minutes.
          </p>
          <button
            onClick={() => setIsSubmitted(false)}
            className="mt-3 text-xs text-indigo-600 font-bold hover:underline"
          >
            Send another link
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Registered Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@example.com"
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-indigo-600 text-white text-xs font-bold rounded-lg shadow-sm hover:bg-indigo-700 transition"
          >
            {loading ? "Generating Reset Token..." : "Send Reset Link"}
          </button>
        </form>
      )}
    </div>
  );
};

export default ForgotPasswordComponent;
