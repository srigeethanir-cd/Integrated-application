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
    height?: number;
    width?: number;
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
      { type: 'header', position: 'top', height: 64 },
      { type: 'content', position: 'center', width: 375, height: 600 },
      { type: 'footer', position: 'bottom', height: 49 },
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
      className="h-screen flex flex-col"
      style={{
        backgroundColor: colorsPalette.background,
      }}
    >
      <header
        className="h-16 flex justify-center items-center"
        style={{
          height: layoutRules.components[0].height,
          backgroundColor: colorsPalette.primary,
        }}
      >
        <h1
          className="text-2xl font-bold"
          style={{
            color: colorsPalette.text,
          }}
        >
          {userStory.title}
        </h1>
      </header>
      <main
        className="flex-1 flex justify-center items-center"
        style={{
          width: layoutRules.components[1].width,
          height: layoutRules.components[1].height,
        }}
      >
        <form
          onSubmit={handleSubmit}
          className="w-full max-w-md p-4 bg-white rounded-lg shadow-md"
          style={{
            padding: designTokens.spacing.medium,
            borderRadius: designTokens.corners.medium,
          }}
        >
          <label
            className="block text-lg font-medium mb-2"
            style={{
              marginBottom: designTokens.spacing.small,
            }}
          >
            Name:
          </label>
          <input
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="block w-full p-2 mb-4 border border-gray-300 rounded-lg"
            style={{
              padding: designTokens.spacing.small,
              borderRadius: designTokens.corners.small,
            }}
          />
          <label
            className="block text-lg font-medium mb-2"
            style={{
              marginBottom: designTokens.spacing.small,
            }}
          >
            Email:
          </label>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="block w-full p-2 mb-4 border border-gray-300 rounded-lg"
            style={{
              padding: designTokens.spacing.small,
              borderRadius: designTokens.corners.small,
            }}
          />
          <label
            className="block text-lg font-medium mb-2"
            style={{
              marginBottom: designTokens.spacing.small,
            }}
          >
            Password:
          </label>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="block w-full p-2 mb-4 border border-gray-300 rounded-lg"
            style={{
              padding: designTokens.spacing.small,
              borderRadius: designTokens.corners.small,
            }}
          />
          <button
            type="submit"
            className="w-full p-2 bg-primary text-white rounded-lg"
            style={{
              backgroundColor: colorsPalette.primary,
              color: colorsPalette.text,
              padding: designTokens.spacing.small,
              borderRadius: designTokens.corners.small,
            }}
          >
            Register
          </button>
        </form>
      </main>
      <footer
        className="h-12 flex justify-center items-center"
        style={{
          height: layoutRules.components[2].height,
          backgroundColor: colorsPalette.secondary,
        }}
      >
        <p
          className="text-sm font-medium"
          style={{
            color: colorsPalette.text,
          }}
        >
          &copy; 2024
        </p>
      </footer>
    </div>
  );
};

export default UserRegistration;