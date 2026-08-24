import React, { useState } from 'react';

interface UserStory {
  story_key: string;
  epic_key: string;
  title: string;
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
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirmation, setPasswordConfirmation] = useState('');

  const handleEmailChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(event.target.value);
  };

  const handlePasswordChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPassword(event.target.value);
  };

  const handlePasswordConfirmationChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPasswordConfirmation(event.target.value);
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    // Validate email format
    if (!/^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i.test(email)) {
      alert('Invalid email format');
      return;
    }
    // Secure password field input
    if (password.length < 8) {
      alert('Password must be at least 8 characters long');
      return;
    }
    // Validate password confirmation match
    if (password !== passwordConfirmation) {
      alert('Passwords do not match');
      return;
    }
    // Submit form
    console.log('Form submitted successfully');
  };

  return (
    <div className="h-screen w-screen flex flex-col items-center justify-center bg-white">
      <header className="w-full h-64 bg-primary text-white flex justify-center items-center">
        <h1 className="text-3xl font-bold">Secure Member Login Integration</h1>
      </header>
      <div className="w-full h-200 bg-hero-image bg-cover bg-center flex justify-center items-center">
        <img src="hero-image.jpg" alt="Hero Image" className="w-full h-full object-cover" />
      </div>
      <div className="w-343 h-100 bg-white shadow-md rounded-md p-4 flex flex-col items-center justify-center">
        <h2 className="text-2xl font-bold mb-4">Member Registration Scaffolding</h2>
        <form onSubmit={handleSubmit} className="w-full flex flex-col items-center justify-center">
          <input
            type="email"
            value={email}
            onChange={handleEmailChange}
            placeholder="Email"
            className="w-full h-12 bg-white border border-gray-400 rounded-md p-2 mb-4"
          />
          <input
            type="password"
            value={password}
            onChange={handlePasswordChange}
            placeholder="Password"
            className="w-full h-12 bg-white border border-gray-400 rounded-md p-2 mb-4"
          />
          <input
            type="password"
            value={passwordConfirmation}
            onChange={handlePasswordConfirmationChange}
            placeholder="Confirm Password"
            className="w-full h-12 bg-white border border-gray-400 rounded-md p-2 mb-4"
          />
          <button
            type="submit"
            className="w-full h-12 bg-primary text-white rounded-md hover:bg-secondary transition duration-300 ease-in-out"
          >
            Register
          </button>
        </form>
      </div>
    </div>
  );
};

export default App;