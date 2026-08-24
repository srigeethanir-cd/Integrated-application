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

const UserRegistration: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const userStory: UserStory = {
    id: 'US001',
    actor: 'User',
    title: 'User Registration',
    epic_key: 'EP001',
    priority: 'High',
    story_key: 'US001',
    description: 'As a new user, I want to register so I can manage tasks.',
    acceptance_criteria: ['Register using name, email, password', 'Email unique'],
  };

  const layoutRules: LayoutRules = {
    type: 'mobile',
    orientation: 'portrait',
    components: [
      { id: 1, type: 'header', x: 0, y: 0, width: 360, height: 64 },
      { id: 2, type: 'hero', x: 0, y: 64, width: 360, height: 200 },
      { id: 3, type: 'content', x: 0, y: 264, width: 360, height: 400 },
      { id: 4, type: 'footer', x: 0, y: 664, width: 360, height: 56 },
    ],
  };

  const colorsPalette: ColorsPalette = {
    primary: '#3498db',
    secondary: '#f1c40f',
    background: '#f9f9f9',
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

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    // Register user logic here
  };

  return (
    <div
      className="h-screen w-screen flex flex-col"
      style={{
        backgroundColor: colorsPalette.background,
      }}
    >
      <header
        className="h-16 w-full flex justify-center items-center"
        style={{
          backgroundColor: colorsPalette.primary,
        }}
      >
        <h1 className="text-2xl text-white">User Registration</h1>
      </header>
      <main
        className="h-full w-full flex flex-col items-center justify-center"
        style={{
          backgroundColor: colorsPalette.background,
        }}
      >
        <form
          onSubmit={handleSubmit}
          className="w-full max-w-md p-4 flex flex-col items-center justify-center"
        >
          <input
            type="text"
            placeholder="Name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="w-full p-2 mb-4 border border-gray-300 rounded"
          />
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="w-full p-2 mb-4 border border-gray-300 rounded"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full p-2 mb-4 border border-gray-300 rounded"
          />
          <button
            type="submit"
            className="w-full p-2 bg-primary text-white rounded"
          >
            Register
          </button>
        </form>
      </main>
      <footer
        className="h-12 w-full flex justify-center items-center"
        style={{
          backgroundColor: colorsPalette.primary,
        }}
      >
        <p className="text-sm text-white">&copy; 2024 User Registration</p>
      </footer>
    </div>
  );
};

export default UserRegistration;