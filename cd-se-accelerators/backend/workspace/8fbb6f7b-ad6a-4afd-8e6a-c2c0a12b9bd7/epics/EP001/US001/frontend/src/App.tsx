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
  { id: 1, type: 'header', x: 0, y: 0, width: 360, height: 64 },
  { id: 2, type: 'hero_image', x: 0, y: 64, width: 360, height: 200 },
  { id: 3, type: 'text_block', x: 16, y: 264, width: 328, height: 100 },
  { id: 4, type: 'call_to_action', x: 16, y: 364, width: 328, height: 44 },
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
    small: 2,
    medium: 4,
    large: 8,
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
    <div className="h-screen w-screen bg-white flex flex-col">
      <header className="h-16 w-full bg-primary text-white flex justify-center items-center">
        <h1 className="text-2xl font-bold">Task Manager</h1>
      </header>
      <div className="h-full w-full flex flex-col justify-center items-center">
        <img
          src="https://via.placeholder.com/360x200"
          alt="Hero Image"
          className="h-48 w-full object-cover"
        />
        <div className="w-80 h-24 bg-white shadow-md rounded-md p-4">
          <h2 className="text-lg font-bold">Register or Login</h2>
          <form className="flex flex-col">
            <input
              type="text"
              placeholder="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="h-8 w-full border border-gray-400 rounded-md p-2 mb-2"
            />
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="h-8 w-full border border-gray-400 rounded-md p-2 mb-2"
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="h-8 w-full border border-gray-400 rounded-md p-2 mb-2"
            />
            <button
              type="button"
              onClick={handleRegister}
              className="h-8 w-full bg-primary text-white rounded-md"
            >
              Register
            </button>
            <button
              type="button"
              onClick={handleLogin}
              className="h-8 w-full bg-secondary text-white rounded-md"
            >
              Login
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default App;