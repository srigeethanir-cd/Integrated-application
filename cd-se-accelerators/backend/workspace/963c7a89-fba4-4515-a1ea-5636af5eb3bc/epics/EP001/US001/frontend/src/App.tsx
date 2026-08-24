import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

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
  type: string;
  orientation: string;
  components: {
    type: string;
    position: string;
  }[];
}

interface ColorPalette {
  primary: string;
  secondary: string;
  background: string;
  text: string;
}

interface DesignToken {
  spacing: {
    margin: number;
    padding: number;
  };
  border_radius: number;
  box_shadow: string;
}

const userStories: UserStory[] = [
  // ... user stories data
];

const layoutRules: LayoutRule = {
  type: 'mobile',
  orientation: 'portrait',
  components: [
    { type: 'navigation_bar', position: 'top' },
    { type: 'hero_section', position: 'below_navigation_bar' },
    { type: 'list', position: 'below_hero_section' },
  ],
};

const colorPalette: ColorPalette = {
  primary: '#3498db',
  secondary: '#f1c40f',
  background: '#ffffff',
  text: '#333333',
};

const designTokens: DesignToken = {
  spacing: {
    margin: 16,
    padding: 8,
  },
  border_radius: 8,
  box_shadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
};

const App: React.FC = () => {
  const [userStoriesList, setUserStoriesList] = useState(userStories);
  const navigate = useNavigate();

  const handleRegister = () => {
    navigate('/register');
  };

  const handleLogin = () => {
    navigate('/login');
  };

  return (
    <div
      style={{
        backgroundColor: colorPalette.background,
        color: colorPalette.text,
        padding: designTokens.spacing.padding,
        margin: designTokens.spacing.margin,
      }}
    >
      <nav
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          backgroundColor: colorPalette.primary,
          color: colorPalette.text,
          padding: designTokens.spacing.padding,
          margin: designTokens.spacing.margin,
          borderRadius: designTokens.border_radius,
          boxShadow: designTokens.box_shadow,
        }}
      >
        <Link to="/" style={{ color: colorPalette.text }}>
          Home
        </Link>
        <button onClick={handleRegister} style={{ backgroundColor: colorPalette.secondary, color: colorPalette.text }}>
          Register
        </button>
        <button onClick={handleLogin} style={{ backgroundColor: colorPalette.secondary, color: colorPalette.text }}>
          Login
        </button>
      </nav>
      <section
        style={{
          marginTop: designTokens.spacing.margin,
          padding: designTokens.spacing.padding,
        }}
      >
        <h1 style={{ color: colorPalette.primary }}>User Stories</h1>
        <ul>
          {userStoriesList.map((userStory) => (
            <li key={userStory.id} style={{ padding: designTokens.spacing.padding, margin: designTokens.spacing.margin }}>
              <h2 style={{ color: colorPalette.primary }}>{userStory.title}</h2>
              <p style={{ color: colorPalette.text }}>{userStory.description}</p>
              <ul>
                {userStory.acceptance_criteria.map((acceptanceCriteria) => (
                  <li key={acceptanceCriteria} style={{ padding: designTokens.spacing.padding, margin: designTokens.spacing.margin }}>
                    {acceptanceCriteria}
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
};

export default App;