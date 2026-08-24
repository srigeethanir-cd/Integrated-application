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
    type: string;
    position: string;
    height: number | string;
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

const layoutRules: LayoutRules = {
  type: 'mobile',
  orientation: 'portrait',
  components: [
    { type: 'navigation_bar', position: 'top', height: 56 },
    { type: 'hero_section', position: 'below_navigation_bar', height: 200 },
    { type: 'list', position: 'below_hero_section', height: 'remaining_screen_height' },
  ],
};

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
    <div className="h-screen bg-white">
      <nav className="fixed top-0 left-0 w-full h-14 bg-primary text-white flex justify-center items-center">
        Navigation Bar
      </nav>
      <div className="h-48 bg-hero mt-14 flex justify-center items-center">
        Hero Section
      </div>
      <div className="flex-1 overflow-y-auto">
        <ul>
          {userStories.map((story) => (
            <li key={story.id} className="p-4 border-b border-gray-200">
              <h2 className="text-lg font-bold">{story.title}</h2>
              <p>{story.description}</p>
              <ul>
                {story.acceptance_criteria.map((criterion) => (
                  <li key={criterion} className="pl-4">
                    {criterion}
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
        <form className="p-4">
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Name"
            className="w-full p-2 border border-gray-200 rounded-sm"
          />
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            className="w-full p-2 border border-gray-200 rounded-sm mt-4"
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            className="w-full p-2 border border-gray-200 rounded-sm mt-4"
          />
          <button
            type="button"
            onClick={handleRegister}
            className="w-full p-2 bg-primary text-white rounded-sm mt-4"
          >
            Register
          </button>
          <button
            type="button"
            onClick={handleLogin}
            className="w-full p-2 bg-secondary text-white rounded-sm mt-4"
          >
            Login
          </button>
        </form>
      </div>
    </div>
  );
};

export default App;