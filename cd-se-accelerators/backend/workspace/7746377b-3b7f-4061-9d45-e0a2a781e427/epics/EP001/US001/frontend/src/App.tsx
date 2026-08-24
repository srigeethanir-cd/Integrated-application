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
  { id: 3, type: 'title', x: 16, y: 264, width: 343, height: 24 },
  { id: 4, type: 'description', x: 16, y: 288, width: 343, height: 48 },
  { id: 5, type: 'call_to_action', x: 16, y: 336, width: 343, height: 48 },
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
    <div
      style={{
        backgroundColor: colorsPalette.background,
        height: '100vh',
        width: '100vw',
      }}
    >
      <header
        style={{
          backgroundColor: colorsPalette.primary,
          height: layoutRules[0].height,
          width: layoutRules[0].width,
          position: 'absolute',
          top: layoutRules[0].y,
          left: layoutRules[0].x,
        }}
      >
        <h1
          style={{
            color: colorsPalette.text,
            fontSize: 24,
            fontWeight: 'bold',
            marginLeft: designTokens.spacing.medium,
          }}
        >
          Task Manager
        </h1>
      </header>
      <div
        style={{
          height: layoutRules[1].height,
          width: layoutRules[1].width,
          position: 'absolute',
          top: layoutRules[1].y,
          left: layoutRules[1].x,
          backgroundImage: 'url(https://via.placeholder.com/375x200)',
          backgroundSize: 'cover',
        }}
      />
      <h2
        style={{
          color: colorsPalette.text,
          fontSize: 18,
          fontWeight: 'bold',
          position: 'absolute',
          top: layoutRules[2].y,
          left: layoutRules[2].x,
        }}
      >
        {userStories[0].title}
      </h2>
      <p
        style={{
          color: colorsPalette.text,
          fontSize: 14,
          position: 'absolute',
          top: layoutRules[3].y,
          left: layoutRules[3].x,
        }}
      >
        {userStories[0].description}
      </p>
      <button
        style={{
          backgroundColor: colorsPalette.primary,
          color: colorsPalette.background,
          fontSize: 16,
          fontWeight: 'bold',
          padding: designTokens.spacing.small,
          borderRadius: designTokens.corners.small,
          position: 'absolute',
          top: layoutRules[4].y,
          left: layoutRules[4].x,
        }}
        onClick={handleRegister}
      >
        Register
      </button>
      <button
        style={{
          backgroundColor: colorsPalette.secondary,
          color: colorsPalette.background,
          fontSize: 16,
          fontWeight: 'bold',
          padding: designTokens.spacing.small,
          borderRadius: designTokens.corners.small,
          position: 'absolute',
          top: layoutRules[4].y + 60,
          left: layoutRules[4].x,
        }}
        onClick={handleLogin}
      >
        Login
      </button>
    </div>
  );
};

export default App;