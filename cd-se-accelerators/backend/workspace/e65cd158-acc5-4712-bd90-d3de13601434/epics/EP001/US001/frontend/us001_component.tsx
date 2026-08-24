typescript
// LoginComponent.tsx
import React, { useState } from 'react';
import axios from 'axios';

interface LoginProps {
  // Add any props if needed
}

const LoginComponent: React.FC<LoginProps> = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const response = await axios.post('/api/login', {
        email,
        password,
      });
      // Handle successful login, e.g., redirect to dashboard
      console.log(response.data);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        setError(error.response?.data);
      } else {
        setError('An error occurred');
      }
    }
  };

  return (
    <div>
      <h1>Login</h1>
      <form onSubmit={handleLogin}>
        <label>
          Email:
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <br />
        <label>
          Password:
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        <br />
        <button type="submit">Login</button>
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </form>
    </div>
  );
};

export default LoginComponent;