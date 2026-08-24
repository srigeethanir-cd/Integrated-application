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
  { id: 'US001', actor: 'User', title: 'User Registration', epic_key: 'EP001', priority: 'High', story_key: 'US001', description: 'As a new user, I want to register so I can manage tasks.', acceptance_criteria: ['Register using name, email, password', 'Email unique'] },
  { id: 'US002', actor: 'User', title: 'User Login', epic_key: 'EP001', priority: 'High', story_key: 'US002', description: 'As a user, I want to log in to access my dashboard.', acceptance_criteria: ['Login with credentials', 'Error on invalid credentials'] },
  { id: 'US003', actor: 'User', title: 'View Dashboard', epic_key: 'EP001', priority: 'Medium', story_key: 'US003', description: 'As a user, I want to see my tasks on a dashboard.', acceptance_criteria: ['Display tasks list', 'Show task count'] },
  { id: 'US004', actor: 'User', title: 'Create Task', epic_key: 'EP001', priority: 'High', story_key: 'US004', description: 'As a user, I want to create a task.', acceptance_criteria: ['Enter task title', 'Task is saved successfully'] },
  { id: 'US005', actor: 'User', title: 'Edit Task', epic_key: 'EP001', priority: 'Medium', story_key: 'US005', description: 'As a user, I want to update task information.', acceptance_criteria: ['Modify task title', 'Modify task status'] },
  { id: 'US006', actor: 'User', title: 'Mark Task Complete', epic_key: 'EP001', priority: 'Medium', story_key: 'US006', description: 'As a user, I want to mark a task as completed.', acceptance_criteria: ['Task status updates to completed'] },
  { id: 'US007', actor: 'User', title: 'Delete Task', epic_key: 'EP001', priority: 'Medium', story_key: 'US007', description: 'As a user, I want to delete tasks.', acceptance_criteria: ['Remove task from database'] },
  { id: 'US008', actor: 'User', title: 'Search Tasks', epic_key: 'EP001', priority: 'Low', story_key: 'US008', description: 'As a user, I want to search tasks by title.', acceptance_criteria: ['Search is case-insensitive', 'Filters list dynamically'] },
  { id: 'US009', actor: 'User', title: 'Filter Tasks', epic_key: 'EP001', priority: 'Low', story_key: 'US009', description: 'As a user, I want to filter tasks by status.', acceptance_criteria: ['Filter by completed or pending status'] },
  { id: 'US010', actor: 'User', title: 'Logout', epic_key: 'EP001', priority: 'High', story_key: 'US010', description: 'As a user, I want to securely log out.', acceptance_criteria: ['Invalidates session', 'Redirects to login page'] },
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
    <div className="app">
      <header className="header" style={{ height: layoutRules[0].height, backgroundColor: colorsPalette.primary }}>
        <h1>Task Manager</h1>
      </header>
      <div className="hero-image" style={{ height: layoutRules[1].height, backgroundImage: 'url(https://via.placeholder.com/375x200)' }} />
      <button className="button" style={{ width: layoutRules[2].width, height: layoutRules[2].height, backgroundColor: colorsPalette.secondary }} onClick={() => handleUserStoryClick(userStories[0])}>
        Create Task
      </button>
      <footer className="footer" style={{ height: layoutRules[3].height, backgroundColor: colorsPalette.primary }}>
        <p>&copy; 2024 Task Manager</p>
      </footer>
      {userStory && (
        <div className="user-story-modal" style={{ padding: designTokens.spacing.medium, borderRadius: designTokens.corners.medium, backgroundColor: colorsPalette.background }}>
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