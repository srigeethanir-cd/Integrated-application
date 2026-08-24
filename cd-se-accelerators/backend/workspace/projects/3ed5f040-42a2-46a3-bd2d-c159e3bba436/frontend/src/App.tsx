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
  { story_key: "US101", epic_key: "EP001", title: "Secure Member Login Integration", acceptance_criteria: ["Validate email format", "Secure password field input"] },
  { story_key: "US102", epic_key: "EP001", title: "Member Registration Scaffolding", acceptance_criteria: ["Validate password confirmation match"] }
];

const layoutRules: LayoutRule[] = [
  { id: 1, type: "header", x: 0, y: 0, width: 375, height: 64 },
  { id: 2, type: "hero_image", x: 0, y: 64, width: 375, height: 200 },
  { id: 3, type: "text_block", x: 16, y: 264, width: 343, height: 100 },
  { id: 4, type: "call_to_action", x: 16, y: 364, width: 343, height: 50 }
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
    if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(email)) {
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
    console.log('Form submitted');
  };

  return (
    <div className="h-screen bg-white">
      <header className="h-16 bg-primary text-white flex justify-center items-center">
        <h1 className="text-2xl font-bold">Secure Member Login</h1>
      </header>
      <div className="h-full flex justify-center items-center">
        <form onSubmit={handleSubmit} className="w-80 h-80 bg-white shadow-md rounded-lg p-4">
          <h2 className="text-lg font-bold mb-4">Login</h2>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="email">
              Email
            </label>
            <input
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              id="email"
              type="email"
              value={email}
              onChange={handleEmailChange}
              placeholder="Enter email"
            />
          </div>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="password">
              Password
            </label>
            <input
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              id="password"
              type="password"
              value={password}
              onChange={handlePasswordChange}
              placeholder="Enter password"
            />
          </div>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="passwordConfirmation">
              Confirm Password
            </label>
            <input
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              id="passwordConfirmation"
              type="password"
              value={passwordConfirmation}
              onChange={handlePasswordConfirmationChange}
              placeholder="Confirm password"
            />
          </div>
          <button
            className="bg-primary hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
            type="submit"
          >
            Login
          </button>
        </form>
      </div>
    </div>
  );
};

export default App;