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
  { id: 3, type: 'button', x: 16, y: 300, width: 343, height: 44 },
  { id: 4, type: 'footer', x: 0, y: 400, width: 375, height: 64 },
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
    <div className="h-screen w-screen flex flex-col">
      <header className="h-16 w-full bg-primary text-white flex justify-center items-center">
        <h1 className="text-2xl font-bold">Task Manager</h1>
      </header>
      <div className="h-full w-full flex justify-center items-center">
        <div className="w-80 h-80 bg-white rounded-lg shadow-lg flex flex-col justify-center items-center">
          <h2 className="text-xl font-bold mb-4">Register or Login</h2>
          <input
            type="text"
            placeholder="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-64 h-10 pl-2 mb-4 border border-gray-400 rounded-lg"
          />
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-64 h-10 pl-2 mb-4 border border-gray-400 rounded-lg"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-64 h-10 pl-2 mb-4 border border-gray-400 rounded-lg"
          />
          <button
            className="w-64 h-10 bg-primary text-white rounded-lg hover:bg-secondary"
            onClick={handleRegister}
          >
            Register
          </button>
          <button
            className="w-64 h-10 bg-primary text-white rounded-lg hover:bg-secondary mt-4"
            onClick={handleLogin}
          >
            Login
          </button>
        </div>
      </div>
      <footer className="h-16 w-full bg-primary text-white flex justify-center items-center">
        <p className="text-sm font-bold">&copy; 2024 Task Manager</p>
      </footer>
    </div>
  );
};

export default App;