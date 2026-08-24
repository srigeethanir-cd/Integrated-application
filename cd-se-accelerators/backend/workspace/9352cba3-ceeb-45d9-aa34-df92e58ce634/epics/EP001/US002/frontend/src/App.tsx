import React, { useState } from 'react';

interface UserStory {
  id: string;
  actor: string;
  title: string;
  epic_key: string;
  priority: string;
  story_key: string;
  description: string;
  acceptance_criteria: string[];
}

interface LayoutRules {
  type: string;
  orientation: string;
  components: {
    id: number;
    type: string;
    x: number;
    y: number;
    width: number;
    height: number;
  }[];
}

interface ColorsPalette {
  primary: string;
  secondary: string;
  background: string;
  text: string;
}

interface DesignTokens {
  spacing: {
    small: number;
    medium: number;
    large: number;
  };
  corners: {
    small: number;
    medium: number;
    large: number;
  };
}

const userStory: UserStory = {
  id: "US002",
  actor: "User",
  title: "User Login",
  epic_key: "EP001",
  priority: "High",
  story_key: "US002",
  description: "As a user, I want to log in to access my dashboard.",
  acceptance_criteria: ["Login with credentials", "Error on invalid credentials"]
};

const layoutRules: LayoutRules = {
  type: "mobile",
  orientation: "portrait",
  components: [
    { id: 1, type: "header", x: 0, y: 0, width: 360, height: 64 },
    { id: 2, type: "hero", x: 0, y: 64, width: 360, height: 200 },
    { id: 3, type: "content", x: 16, y: 264, width: 328, height: 400 },
    { id: 4, type: "footer", x: 0, y: 664, width: 360, height: 56 }
  ]
};

const colorsPalette: ColorsPalette = {
  primary: "#3498db",
  secondary: "#f1c40f",
  background: "#f9f9f9",
  text: "#333333"
};

const designTokens: DesignTokens = {
  spacing: {
    small: 8,
    medium: 16,
    large: 24
  },
  corners: {
    small: 2,
    medium: 4,
    large: 8
  }
};

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (username === '' || password === '') {
      setError('Please fill in all fields');
    } else {
      // Login logic here
      console.log('Login successful');
    }
  };

  return (
    <div className="h-screen flex flex-col">
      <header className="h-16 bg-primary text-white p-4 flex justify-center">
        <h1 className="text-2xl font-bold">Login</h1>
      </header>
      <main className="flex-1 flex justify-center items-center">
        <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow-md w-80">
          <h2 className="text-lg font-bold mb-4">Login</h2>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="username">
              Username
            </label>
            <input
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              id="username"
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
            />
          </div>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="password">
              Password
            </label>
            <input
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline"
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>
          {error && <p className="text-red-500 text-xs italic mb-4">{error}</p>}
          <button
            className="bg-primary hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
            type="submit"
          >
            Login
          </button>
        </form>
      </main>
      <footer className="h-16 bg-primary text-white p-4 flex justify-center">
        <p className="text-sm">&copy; 2024</p>
      </footer>
    </div>
  );
};

export default LoginPage;