import React, { useState } from 'react';

export default function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Logging in:', email);
  };

  return (
    <form onSubmit={handleLogin} className="space-y-4">
      <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} className="w-full p-2 border rounded" required />
      <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} className="w-full p-2 border rounded" required />
      <button type="submit" className="w-full bg-blue-600 text-white p-2 rounded font-bold">Log In</button>
    </form>
  );
}
