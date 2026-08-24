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

const userStories: UserStory[] = [
  {
    id: 'US001',
    actor: 'User',
    title: 'User Registration',
    epic_key: 'EP001',
    priority: 'High',
    story_key: 'US001',
    description: 'As a new user, I want to register so I can manage tasks.',
    acceptance_criteria: ['Register using name, email, password', 'Email unique'],
  },
  {
    id: 'US002',
    actor: 'User',
    title: 'User Login',
    epic_key: 'EP001',
    priority: 'High',
    story_key: 'US002',
    description: 'As a user, I want to log in to access my dashboard.',
    acceptance_criteria: ['Login with credentials', 'Error on invalid credentials'],
  },
];

const layoutRules: LayoutRule[] = [
  { id: 1, type: 'header', x: 0, y: 0, width: 375, height: 64 },
  { id: 2, type: 'hero_image', x: 0, y: 64, width: 375, height: 200 },
  { id: 3, type: 'text_block', x: 16, y: 264, width: 343, height: 100 },
  { id: 4, type: 'call_to_action', x: 16, y: 364, width: 343, height: 50 },
];

const colorsPalette: ColorsPalette = {
  primary: '#3498db',
  secondary: '#f1c40f',
  background: '#ffffff',
  text: '#333333',
};

const designTokens: DesignTokens = {
  spacing: {
    small: 8,
    medium: 16,
    large: 24,
  },
  corners: {
    small: 4,
    medium: 8,
    large: 12,
  },
};

const App: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleRegister = () => {
    // Register logic
  };

  const handleLogin = () => {
    // Login logic
  };

  return (
    <div className="h-screen w-screen flex flex-col items-center justify-center bg-white">
      <header className="w-full h-64 bg-primary flex justify-center items-center">
        <h1 className="text-3xl text-white">User Registration</h1>
      </header>
      <div className="w-full h-200 bg-hero-image bg-cover bg-center flex justify-center items-center">
        <img src="hero-image.jpg" alt="Hero Image" />
      </div>
      <div className="w-343 h-100 bg-white shadow-md rounded-md p-4 flex flex-col items-center justify-center">
        <h2 className="text-2xl text-text">Register</h2>
        <input
          type="text"
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full h-10 bg-gray-100 p-2 rounded-md mb-4"
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full h-10 bg-gray-100 p-2 rounded-md mb-4"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full h-10 bg-gray-100 p-2 rounded-md mb-4"
        />
        <button
          onClick={handleRegister}
          className="w-full h-10 bg-primary text-white rounded-md hover:bg-secondary"
        >
          Register
        </button>
      </div>
      <div className="w-343 h-50 bg-white shadow-md rounded-md p-4 flex flex-col items-center justify-center">
        <h2 className="text-2xl text-text">Login</h2>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full h-10 bg-gray-100 p-2 rounded-md mb-4"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full h-10 bg-gray-100 p-2 rounded-md mb-4"
        />
        <button
          onClick={handleLogin}
          className="w-full h-10 bg-primary text-white rounded-md hover:bg-secondary"
        >
          Login
        </button>
      </div>
    </div>
  );
};

export default App;