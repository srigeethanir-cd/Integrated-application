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

interface Colors {
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

const colors: Colors = {
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
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleLogin = () => {
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
    if (password !== confirmPassword) {
      alert('Passwords do not match');
      return;
    }

    // Login logic here
  };

  return (
    <div className="h-screen bg-white">
      <header className="h-16 bg-primary text-white flex justify-center items-center">
        <h1 className="text-2xl font-bold">Secure Member Login</h1>
      </header>
      <div className="h-64 bg-hero-image bg-cover bg-center"></div>
      <div className="px-4 py-8">
        <h2 className="text-xl font-bold mb-4">Login</h2>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          className="w-full p-2 mb-4 border border-gray-400 rounded"
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="w-full p-2 mb-4 border border-gray-400 rounded"
        />
        <input
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder="Confirm Password"
          className="w-full p-2 mb-4 border border-gray-400 rounded"
        />
        <button
          onClick={handleLogin}
          className="w-full p-2 bg-primary text-white rounded"
        >
          Login
        </button>
      </div>
    </div>
  );
};

export default App;