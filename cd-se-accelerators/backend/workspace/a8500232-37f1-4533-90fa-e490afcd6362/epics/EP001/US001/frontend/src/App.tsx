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
  grid_system: string;
  sections: {
    name: string;
    height: string;
    width: string;
    position: string;
  }[];
}

interface ColorsPalette {
  primary_color: string;
  secondary_color: string;
  background_color: string;
  text_color: string;
}

interface DesignTokens {
  spacing: {
    margin: string;
    padding: string;
  };
  border_radius: string;
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
    grid_system: '12-column',
    sections: [
      { name: 'Navigation Bar', height: '56px', width: '100%', position: 'top' },
      { name: 'Hero Section', height: '300px', width: '100%', position: 'below Navigation Bar' },
      { name: 'Content Area', height: 'flexible', width: '100%', position: 'below Hero Section' },
    ],
  };
  const colorsPalette: ColorsPalette = {
    primary_color: '#3498db',
    secondary_color: '#f1c40f',
    background_color: '#ffffff',
    text_color: '#333333',
  };
  const designTokens: DesignTokens = {
    spacing: { margin: '16px', padding: '16px' },
    border_radius: '4px',
  };

  const handleRegistration = () => {
    // Implement registration logic here
    console.log('Registration submitted:', { name, email, password });
  };

  return (
    <div
      className="h-screen w-screen flex flex-col"
      style={{
        backgroundColor: colorsPalette.background_color,
      }}
    >
      {/* Navigation Bar */}
      <div
        className="h-14 w-full flex justify-center items-center"
        style={{
          height: layoutRules.sections[0].height,
          backgroundColor: colorsPalette.primary_color,
        }}
      >
        <h1 className="text-2xl text-white">Registration</h1>
      </div>

      {/* Hero Section */}
      <div
        className="h-64 w-full flex justify-center items-center"
        style={{
          height: layoutRules.sections[1].height,
          backgroundColor: colorsPalette.secondary_color,
        }}
      >
        <h2 className="text-3xl text-white">{userStory.title}</h2>
      </div>

      {/* Content Area */}
      <div
        className="h-full w-full flex flex-col justify-center items-center"
        style={{
          height: layoutRules.sections[2].height,
          padding: designTokens.spacing.padding,
        }}
      >
        <form
          className="w-full max-w-md flex flex-col justify-center items-center"
          onSubmit={handleRegistration}
        >
          <input
            type="text"
            placeholder="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full p-2 mb-4 border border-gray-300 rounded"
            style={{
              borderRadius: designTokens.border_radius,
              padding: designTokens.spacing.padding,
            }}
          />
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full p-2 mb-4 border border-gray-300 rounded"
            style={{
              borderRadius: designTokens.border_radius,
              padding: designTokens.spacing.padding,
            }}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-2 mb-4 border border-gray-300 rounded"
            style={{
              borderRadius: designTokens.border_radius,
              padding: designTokens.spacing.padding,
            }}
          />
          <button
            type="submit"
            className="w-full p-2 bg-primary_color text-white rounded"
            style={{
              backgroundColor: colorsPalette.primary_color,
              borderRadius: designTokens.border_radius,
              padding: designTokens.spacing.padding,
            }}
          >
            Register
          </button>
        </form>
      </div>
    </div>
  );
};

export default UserRegistration;