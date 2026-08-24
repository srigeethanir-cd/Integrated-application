typescript
// Component: UserLogin.tsx
import React, { useState } from 'react';
import axios from 'axios';

interface LoginCredentials {
  email: string;
  password: string;
}

const UserLogin: React.FC = () => {
  const [loginCredentials, setLoginCredentials] = useState<LoginCredentials>({
    email: '',
    password: '',
  });
  const [loginError, setLoginError] = useState<string | null>(null);

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setLoginCredentials({ ...loginCredentials, [name]: value });
  };

  const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const response = await axios.post('/api/login', loginCredentials);
      // Handle successful login response
      console.log(response.data);
    } catch (error: any) {
      if (error.response) {
        setLoginError(error.response.data.error);
      } else {
        setLoginError('An error occurred while logging in');
      }
    }
  };

  return (
    <div>
      <h1>Login</h1>
      <form onSubmit={handleLogin}>
        <label>
          Email:
          <input
            type="email"
            name="email"
            value={loginCredentials.email}
            onChange={handleInputChange}
          />
        </label>
        <br />
        <label>
          Password:
          <input
            type="password"
            name="password"
            value={loginCredentials.password}
            onChange={handleInputChange}
          />
        </label>
        <br />
        <button type="submit">Login</button>
        {loginError && <p style={{ color: 'red' }}>{loginError}</p>}
      </form>
    </div>
  );
};

export default UserLogin;