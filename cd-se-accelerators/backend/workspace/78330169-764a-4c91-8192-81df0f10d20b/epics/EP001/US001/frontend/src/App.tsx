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
  {
    id: 'US003',
    actor: 'User',
    title: 'View Dashboard',
    epic_key: 'EP001',
    priority: 'Medium',
    story_key: 'US003',
    description: 'As a user, I want to see my tasks on a dashboard.',
    acceptance_criteria: ['Display tasks list', 'Show task count'],
  },
  {
    id: 'US004',
    actor: 'User',
    title: 'Create Task',
    epic_key: 'EP001',
    priority: 'High',
    story_key: 'US004',
    description: 'As a user, I want to create a task.',
    acceptance_criteria: ['Enter task title', 'Task is saved successfully'],
  },
];

const layoutRules: LayoutRule[] = [
  { id: 1, type: 'header', x: 0, y: 0, width: 375, height: 64 },
  { id: 2, type: 'hero_image', x: 0, y: 64, width: 375, height: 200 },
  { id: 3, type: 'button', x: 100, y: 300, width: 175, height: 50 },
  { id: 4, type: 'footer', x: 0, y: 450, width: 375, height: 50 },
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
  const [userStory, setUserStory] = useState<UserStory | null>(null);

  const handleUserStoryClick = (story: UserStory) => {
    setUserStory(story);
  };

  return (
    <div
      style={{
        backgroundColor: colorsPalette.background,
        height: '100vh',
        width: '100vw',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <header
        style={{
          width: layoutRules[0].width,
          height: layoutRules[0].height,
          backgroundColor: colorsPalette.primary,
          color: colorsPalette.text,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        Header
      </header>
      <div
        style={{
          width: layoutRules[1].width,
          height: layoutRules[1].height,
          backgroundColor: colorsPalette.secondary,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        Hero Image
      </div>
      <button
        style={{
          width: layoutRules[2].width,
          height: layoutRules[2].height,
          backgroundColor: colorsPalette.primary,
          color: colorsPalette.text,
          borderRadius: designTokens.corners.medium,
          padding: designTokens.spacing.small,
        }}
        onClick={() => handleUserStoryClick(userStories[0])}
      >
        Click me
      </button>
      {userStory && (
        <div
          style={{
            width: layoutRules[3].width,
            height: layoutRules[3].height,
            backgroundColor: colorsPalette.background,
            color: colorsPalette.text,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
          }}
        >
          <p>{userStory.description}</p>
        </div>
      )}
      <footer
        style={{
          width: layoutRules[3].width,
          height: layoutRules[3].height,
          backgroundColor: colorsPalette.primary,
          color: colorsPalette.text,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        Footer
      </footer>
    </div>
  );
};

export default App;