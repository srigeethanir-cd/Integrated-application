typescript
// Component.tsx
import React, { useState } from 'react';
import axios from 'axios';

interface LoginCredentials {
  username: string;
  password: string;
}

const LoginComponent: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const response = await axios.post('/api/login', {
        username,
        password,
      });
      if (response.status === 200) {
        setIsLoggedIn(true);
        // Redirect to dashboard
        window.location.href = '/dashboard';
      } else {
        setError('Invalid credentials');
      }
    } catch (error) {
      setError('Invalid credentials');
    }
  };

  return (
    <div>
      <h1>Login</h1>
      <form onSubmit={handleLogin}>
        <label>Username:</label>
        <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} />
        <br />
        <label>Password:</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <br />
        <button type="submit">Login</button>
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </form>
    </div>
  );
};

export default LoginComponent;