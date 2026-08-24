typescript
// Component: UserLogin.tsx
import React, { useState } from 'react';
import axios from 'axios';

interface LoginCredentials {
  username: string;
  password: string;
}

const UserLogin: React.FC = () => {
  const [credentials, setCredentials] = useState<LoginCredentials>({
    username: '',
    password: '',
  });
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const response = await axios.post('/api/login', credentials);
      if (response.status === 200) {
        // Login successful, redirect to dashboard
        window.location.href = '/dashboard';
      } else {
        throw new Error('Invalid credentials');
      }
    } catch (error: any) {
      setError(error.message);
    }
  };

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setCredentials({ ...credentials, [name]: value });
  };

  return (
    <div>
      <h1>Login</h1>
      <form onSubmit={handleLogin}>
        <label>
          Username:
          <input
            type="text"
            name="username"
            value={credentials.username}
            onChange={handleInputChange}
          />
        </label>
        <br />
        <label>
          Password:
          <input
            type="password"
            name="password"
            value={credentials.password}
            onChange={handleInputChange}
          />
        </label>
        <br />
        <button type="submit">Login</button>
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </form>
    </div>
  );
};

export default UserLogin;