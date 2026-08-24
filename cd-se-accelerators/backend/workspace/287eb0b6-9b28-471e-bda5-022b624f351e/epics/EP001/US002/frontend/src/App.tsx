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
    { id: 1, type: "header", x: 0, y: 0, width: 360, height: 64 },
    { id: 2, type: "hero_image", x: 0, y: 64, width: 360, height: 200 },
    { id: 3, type: "text_block", x: 16, y: 264, width: 328, height: 120 },
    { id: 4, type: "call_to_action", x: 16, y: 384, width: 328, height: 48 }
  ]
};

const colorsPalette: ColorsPalette = {
  primary: "#3498db",
  secondary: "#f1c40f",
  background: "#f9f9f9",
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
    <div className="h-screen w-screen flex flex-col items-center justify-center bg-background">
      <header className="w-full h-64 flex justify-center items-center">
        <h1 className="text-3xl text-primary">{userStory.title}</h1>
      </header>
      <div className="w-full h-200 flex justify-center items-center">
        <img src="hero_image.jpg" alt="Hero Image" className="w-full h-full object-cover" />
      </div>
      <div className="w-328 h-120 flex flex-col items-center justify-center">
        <p className="text-text">{userStory.description}</p>
      </div>
      <div className="w-328 h-48 flex justify-center items-center">
        <button className="bg-primary text-white py-2 px-4 rounded-md" onClick={handleLogin}>Login</button>
        {error && <p className="text-red-500">{error}</p>}
      </div>
    </div>
  );
};

export default LoginPage;