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
  // ... user stories data
];

const layoutRules: LayoutRule[] = [
  // ... layout rules data
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
        <h1>Task Manager</h1>
      </header>
      <main className="main">
        <section className="hero">
          <img src="hero-image.jpg" alt="Hero Image" />
        </section>
        <section className="user-stories">
          {userStories.map((story) => (
            <div key={story.id} onClick={() => handleUserStoryClick(story)}>
              <h2>{story.title}</h2>
              <p>{story.description}</p>
            </div>
          ))}
        </section>
        {userStory && (
          <section className="user-story-details">
            <h2>{userStory.title}</h2>
            <p>{userStory.description}</p>
            <ul>
              {userStory.acceptance_criteria.map((criterion) => (
                <li key={criterion}>{criterion}</li>
              ))}
            </ul>
          </section>
        )}
      </main>
      <footer className="footer">
        <p>&copy; 2023 Task Manager</p>
      </footer>
    </div>
  );
};

export default App;