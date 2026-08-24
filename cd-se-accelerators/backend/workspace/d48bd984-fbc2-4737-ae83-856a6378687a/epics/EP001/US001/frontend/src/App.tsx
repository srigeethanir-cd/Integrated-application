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
      { id: 2, type: 'hero_image', x: 0, y: 64, width: 360, height: 200 },
      { id: 3, type: 'button', x: 16, y: 300, width: 328, height: 48 },
      { id: 4, type: 'footer', x: 0, y: 400, width: 360, height: 64 },
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
          height: layoutRules.components[0].height,
          width: layoutRules.components[0].width,
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
      <div
        className="h-48 w-full flex justify-center items-center"
        style={{
          height: layoutRules.components[1].height,
          width: layoutRules.components[1].width,
        }}
      >
        <img
          src="https://via.placeholder.com/360x200"
          alt="Hero Image"
          className="h-full w-full object-cover"
        />
      </div>
      <form
        onSubmit={handleSubmit}
        className="h-12 w-full flex flex-col justify-center items-center"
        style={{
          height: layoutRules.components[2].height,
          width: layoutRules.components[2].width,
          marginLeft: designTokens.spacing.small,
        }}
      >
        <input
          type="text"
          placeholder="Name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          className="h-8 w-full mb-2 p-2 border border-gray-400 rounded"
          style={{
            borderColor: colorsPalette.text,
          }}
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="h-8 w-full mb-2 p-2 border border-gray-400 rounded"
          style={{
            borderColor: colorsPalette.text,
          }}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="h-8 w-full mb-2 p-2 border border-gray-400 rounded"
          style={{
            borderColor: colorsPalette.text,
          }}
        />
        <button
          type="submit"
          className="h-8 w-full bg-blue-500 text-white rounded"
          style={{
            backgroundColor: colorsPalette.primary,
          }}
        >
          Register
        </button>
      </form>
      <footer
        className="h-16 w-full flex justify-center items-center"
        style={{
          height: layoutRules.components[3].height,
          width: layoutRules.components[3].width,
        }}
      >
        <p
          className="text-sm font-bold"
          style={{
            color: colorsPalette.text,
          }}
        >
          &copy; 2024 User Registration
        </p>
      </footer>
    </div>
  );
};

export default UserRegistration;