typescript
// LoginComponent.tsx
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

  const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const response = await axios.post('/api/login', {
        username,
        password,
      });
      if (response.status === 200) {
        // Login successful, redirect to dashboard
        window.location.href = '/dashboard';
      } else {
        throw new Error('Invalid credentials');
      }
    } catch (error) {
      setError('Invalid username or password');
    }
  };

  return (
    <div>
      <h1>Login</h1>
      <form onSubmit={handleLogin}>
        <label>
          Username:
          <input
            type="text"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
          />
        </label>
        <br />
        <label>
          Password:
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        <br />
        <button type="submit">Login</button>
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </form>
    </div>
  );
};

export default LoginComponent;