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

interface LayoutRule {
  id: number;
  type: string;
  x: number;
  y: number;
  width: number;
  height: number;
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

const layoutRules: LayoutRule[] = [
  { id: 1, type: "header", x: 0, y: 0, width: 375, height: 64 },
  { id: 2, type: "hero_image", x: 0, y: 64, width: 375, height: 200 },
  { id: 3, type: "title", x: 16, y: 264, width: 343, height: 24 },
  { id: 4, type: "description", x: 16, y: 288, width: 343, height: 48 },
  { id: 5, type: "call_to_action", x: 16, y: 336, width: 343, height: 48 }
];

const colorsPalette: ColorsPalette = {
  primary: "#3498db",
  secondary: "#f1c40f",
  background: "#ffffff",
  text: "#333333"
};

const designTokens: DesignTokens = {
  spacing: {
    small: 8,
    medium: 16,
    large: 24
  },
  corners: {
    small: 4,
    medium: 8,
    large: 12
  }
};

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = () => {
    if (username === 'admin' && password === 'password') {
      // Login successful
    } else {
      setError('Invalid credentials');
    }
  };

  return (
    <div className="h-screen bg-white">
      <header className="h-16 bg-primary text-white flex justify-center items-center">
        <h1 className="text-2xl font-bold">Login</h1>
      </header>
      <div className="h-full flex justify-center items-center">
        <div className="w-80 h-80 bg-white shadow-md rounded-lg p-4">
          <h2 className="text-lg font-bold mb-2">Login</h2>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full p-2 mb-2 border border-gray-400 rounded-lg"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-2 mb-2 border border-gray-400 rounded-lg"
          />
          {error && <p className="text-red-500 mb-2">{error}</p>}
          <button
            onClick={handleLogin}
            className="w-full p-2 bg-primary text-white rounded-lg hover:bg-secondary"
          >
            Login
          </button>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;