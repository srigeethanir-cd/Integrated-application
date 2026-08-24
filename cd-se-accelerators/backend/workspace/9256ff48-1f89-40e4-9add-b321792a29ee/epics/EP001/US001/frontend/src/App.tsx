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
      { id: 1, type: 'header', x: 0, y: 0, width: 375, height: 64 },
      { id: 2, type: 'hero_image', x: 0, y: 64, width: 375, height: 200 },
      { id: 3, type: 'text_block', x: 16, y: 264, width: 343, height: 100 },
      { id: 4, type: 'call_to_action', x: 16, y: 364, width: 343, height: 50 },
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

  const handleRegistration = () => {
    // Register user logic
  };

  return (
    <div
      className="h-screen w-screen bg-white flex flex-col"
      style={{ backgroundColor: colorsPalette.background }}
    >
      <header
        className="h-16 w-full bg-white flex justify-center items-center"
        style={{ height: layoutRules.components[0].height }}
      >
        <h1 className="text-2xl font-bold" style={{ color: colorsPalette.text }}>
          {userStory.title}
        </h1>
      </header>
      <div
        className="h-50 w-full bg-white flex justify-center items-center"
        style={{ height: layoutRules.components[1].height }}
      >
        <img
          src="https://via.placeholder.com/300"
          alt="Hero Image"
          className="h-full w-full object-cover"
        />
      </div>
      <div
        className="w-80 h-20 bg-white flex flex-col justify-center items-center"
        style={{
          width: layoutRules.components[2].width,
          height: layoutRules.components[2].height,
          marginLeft: designTokens.spacing.medium,
        }}
      >
        <p className="text-lg font-medium" style={{ color: colorsPalette.text }}>
          {userStory.description}
        </p>
      </div>
      <div
        className="w-80 h-10 bg-primary flex justify-center items-center"
        style={{
          width: layoutRules.components[3].width,
          height: layoutRules.components[3].height,
          marginLeft: designTokens.spacing.medium,
          backgroundColor: colorsPalette.primary,
          borderRadius: designTokens.corners.medium,
        }}
      >
        <button
          className="text-lg font-medium text-white"
          onClick={handleRegistration}
        >
          Register
        </button>
      </div>
      <form
        className="w-80 h-20 bg-white flex flex-col justify-center items-center"
        style={{
          width: layoutRules.components[2].width,
          height: layoutRules.components[2].height,
          marginLeft: designTokens.spacing.medium,
        }}
      >
        <input
          type="text"
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full h-10 bg-white border border-gray-300 rounded-md"
          style={{
            marginBottom: designTokens.spacing.small,
          }}
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full h-10 bg-white border border-gray-300 rounded-md"
          style={{
            marginBottom: designTokens.spacing.small,
          }}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full h-10 bg-white border border-gray-300 rounded-md"
        />
      </form>
    </div>
  );
};

export default UserRegistration;