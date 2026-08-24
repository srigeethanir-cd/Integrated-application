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
  // Add user stories here
];

const layoutRules: LayoutRule[] = [
  // Add layout rules here
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
    <div className="app">
      <header className="header">
        <h1>Task Management</h1>
      </header>
      <div className="hero-image">
        <img src="hero-image.jpg" alt="Hero Image" />
      </div>
      <div className="text-block">
        <p>
          Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed sit amet nulla auctor, vestibulum magna sed, convallis ex.
        </p>
      </div>
      <div className="call-to-action">
        <button onClick={() => handleUserStoryClick(userStories[0])}>
          Get Started
        </button>
      </div>
      {userStory && (
        <div className="user-story-modal">
          <h2>{userStory.title}</h2>
          <p>{userStory.description}</p>
          <ul>
            {userStory.acceptance_criteria.map((criterion, index) => (
              <li key={index}>{criterion}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default App;