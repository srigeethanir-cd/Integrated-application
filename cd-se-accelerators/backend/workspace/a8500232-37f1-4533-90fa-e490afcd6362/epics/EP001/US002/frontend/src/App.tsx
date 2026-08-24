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
    { id: 1, type: "header", x: 0, y: 0, width: 375, height: 64 },
    { id: 2, type: "hero_image", x: 0, y: 64, width: 375, height: 200 },
    { id: 3, type: "button", x: 100, y: 300, width: 175, height: 50 },
    { id: 4, type: "footer", x: 0, y: 450, width: 375, height: 50 }
  ]
};

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
      // Login success
    } else {
      setError('Invalid credentials');
    }
  };

  return (
    <div className="h-screen w-screen flex flex-col">
      <header className="h-16 bg-primary text-white flex justify-center items-center">
        <h1 className="text-2xl font-bold">Login</h1>
      </header>
      <div className="flex-1 flex justify-center items-center">
        <img src="hero_image.jpg" alt="Hero Image" className="h-48 w-48" />
      </div>
      <div className="flex justify-center items-center mb-8">
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          className="px-4 py-2 border border-gray-400 rounded-lg w-64"
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="px-4 py-2 border border-gray-400 rounded-lg w-64 mt-4"
        />
        <button
          onClick={handleLogin}
          className="bg-primary text-white px-4 py-2 rounded-lg w-64 mt-4"
        >
          Login
        </button>
        {error && <p className="text-red-500 mt-4">{error}</p>}
      </div>
      <footer className="h-12 bg-secondary text-white flex justify-center items-center">
        <p className="text-sm font-bold">Copyright 2024</p>
      </footer>
    </div>
  );
};

export default LoginPage;