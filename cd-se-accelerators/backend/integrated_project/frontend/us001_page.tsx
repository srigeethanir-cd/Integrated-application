typescript
// Component: UserLogin.tsx
import React, { useState } from 'react';
import axios from 'axios';

interface LoginCredentials {
  email: string;
  password: string;
}

const UserLogin: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState(null);

  const handleEmailChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(event.target.value);
  };

  const handlePasswordChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPassword(event.target.value);
  };

  const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const response = await axios.post('/api/login', {
        email,
        password,
      });
      // Handle successful login
      console.log(response.data);
      // Redirect to protected route or update local state
    } catch (error) {
      if (axios.isAxiosError(error)) {
        setLoginError(error.response?.data);
      } else {
        setLoginError('An unknown error occurred');
      }
    }
  };

  return (
    <div>
      <h1>Login</h1>
      <form onSubmit={handleLogin}>
        <label>
          Email:
          <input type="email" value={email} onChange={handleEmailChange} />
        </label>
        <br />
        <label>
          Password:
          <input type="password" value={password} onChange={handlePasswordChange} />
        </label>
        <br />
        <button type="submit">Login</button>
        {loginError && <p style={{ color: 'red' }}>{loginError}</p>}
      </form>
    </div>
  );
};

export default UserLogin;