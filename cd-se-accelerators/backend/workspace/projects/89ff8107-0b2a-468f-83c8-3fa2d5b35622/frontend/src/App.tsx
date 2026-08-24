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
      alert('Password confirmation does not match');
      return;
    }
    // Submit form
    console.log('Form submitted');
  };

  return (
    <div className="h-screen bg-white">
      <header className="h-16 bg-white border-b border-gray-200">
        <h1 className="text-3xl font-bold text-gray-800">Secure Member Login</h1>
      </header>
      <main className="h-full p-4">
        <form onSubmit={handleSubmit} className="max-w-md mx-auto p-4 bg-white rounded-lg shadow-md">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="email">
            Email
          </label>
          <input
            className="block w-full p-2 border border-gray-200 rounded-lg focus:outline-none focus:ring focus:ring-blue-500"
            type="email"
            id="email"
            value={email}
            onChange={handleEmailChange}
          />
          <label className="block text-gray-700 text-sm font-bold mb-2 mt-4" htmlFor="password">
            Password
          </label>
          <input
            className="block w-full p-2 border border-gray-200 rounded-lg focus:outline-none focus:ring focus:ring-blue-500"
            type="password"
            id="password"
            value={password}
            onChange={handlePasswordChange}
          />
          <label className="block text-gray-700 text-sm font-bold mb-2 mt-4" htmlFor="passwordConfirmation">
            Confirm Password
          </label>
          <input
            className="block w-full p-2 border border-gray-200 rounded-lg focus:outline-none focus:ring focus:ring-blue-500"
            type="password"
            id="passwordConfirmation"
            value={passwordConfirmation}
            onChange={handlePasswordConfirmationChange}
          />
          <button
            className="w-full p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring focus:ring-blue-500"
            type="submit"
          >
            Submit
          </button>
        </form>
      </main>
    </div>
  );
};

export default App;