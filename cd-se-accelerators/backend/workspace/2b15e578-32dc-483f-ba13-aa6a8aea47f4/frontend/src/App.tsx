import React, { useState } from 'react';

interface UserStory {
  story_key: string;
  epic_key: string;
  title: string;
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
    story_key: 'US101',
    epic_key: 'EP001',
    title: 'Secure Member Login Integration',
    acceptance_criteria: ['Validate email format', 'Secure password field input'],
  },
  {
    story_key: 'US102',
    epic_key: 'EP001',
    title: 'Member Registration Scaffolding',
    acceptance_criteria: ['Validate password confirmation match'],
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
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleEmailChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(event.target.value);
  };

  const handlePasswordChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPassword(event.target.value);
  };

  const handleConfirmPasswordChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setConfirmPassword(event.target.value);
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    // Validate email format
    if (!email.includes('@')) {
      alert('Invalid email format');
      return;
    }
    // Secure password field input
    if (password.length < 8) {
      alert('Password must be at least 8 characters long');
      return;
    }
    // Validate password confirmation match
    if (password !== confirmPassword) {
      alert('Passwords do not match');
      return;
    }
    // Submit form
    console.log('Form submitted successfully');
  };

  return (
    <div className="h-screen bg-white">
      <nav className="bg-primary text-white p-4 flex justify-between items-center">
        <h1 className="text-lg font-bold">Secure Member Login</h1>
      </nav>
      <section className="h-200 bg-hero bg-cover bg-center">
        <h2 className="text-3xl font-bold text-white p-4">Hero Section</h2>
      </section>
      <ul className="list-none p-4">
        {userStories.map((story, index) => (
          <li key={index} className="mb-4">
            <h3 className="text-xl font-bold">{story.title}</h3>
            <ul className="list-none pl-4">
              {story.acceptance_criteria.map((criterion, index) => (
                <li key={index} className="mb-2">
                  {criterion}
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
      <form onSubmit={handleSubmit} className="p-4">
        <label className="block text-lg font-bold mb-2" htmlFor="email">
          Email:
        </label>
        <input
          type="email"
          id="email"
          value={email}
          onChange={handleEmailChange}
          className="block w-full p-2 border border-gray-400 rounded-sm"
        />
        <label className="block text-lg font-bold mb-2" htmlFor="password">
          Password:
        </label>
        <input
          type="password"
          id="password"
          value={password}
          onChange={handlePasswordChange}
          className="block w-full p-2 border border-gray-400 rounded-sm"
        />
        <label className="block text-lg font-bold mb-2" htmlFor="confirmPassword">
          Confirm Password:
        </label>
        <input
          type="password"
          id="confirmPassword"
          value={confirmPassword}
          onChange={handleConfirmPasswordChange}
          className="block w-full p-2 border border-gray-400 rounded-sm"
        />
        <button
          type="submit"
          className="bg-primary text-white p-2 rounded-sm w-full mt-4"
        >
          Submit
        </button>
      </form>
    </div>
  );
};

export default App;