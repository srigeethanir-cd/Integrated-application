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
    { id: 3, type: "text_block", x: 16, y: 264, width: 343, height: 100 },
    { id: 4, type: "call_to_action", x: 16, y: 364, width: 343, height: 50 }
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
    <div className="h-screen bg-white">
      <header className="h-16 bg-primary text-white flex justify-center items-center">
        <h1 className="text-2xl">{userStory.title}</h1>
      </header>
      <div className="h-50 flex justify-center items-center">
        <img src="hero_image.jpg" alt="Hero Image" className="h-50 w-full object-cover" />
      </div>
      <div className="px-4 py-6">
        <h2 className="text-xl text-primary">{userStory.description}</h2>
        <form className="mt-4">
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full p-2 border border-gray-400 rounded-sm"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-2 border border-gray-400 rounded-sm mt-4"
          />
          {error && <p className="text-red-500 mt-2">{error}</p>}
          <button
            type="button"
            onClick={handleLogin}
            className="w-full p-2 bg-primary text-white rounded-sm mt-4"
          >
            Login
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;