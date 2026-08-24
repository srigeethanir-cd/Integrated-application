import React, { useState, useEffect } from 'react';

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
    height: number | string;
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

const layoutRules: LayoutRules = {
  type: 'mobile',
  orientation: 'portrait',
  components: [
    { type: 'navigation_bar', position: 'top', height: 56 },
    { type: 'hero_section', position: 'below_navigation_bar', height: 200 },
    { type: 'list', position: 'below_hero_section', height: 'remaining_screen_height' },
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

const App: React.FC = () => {
  const [userStoriesList, setUserStoriesList] = useState(userStories);

  return (
    <div className="h-screen flex flex-col">
      <nav className="bg-primary text-white p-4 flex justify-between">
        <h1 className="text-2xl font-bold">Task Manager</h1>
        <button className="bg-secondary text-white p-2 rounded">Logout</button>
      </nav>
      <section className="bg-hero h-64 flex justify-center items-center">
        <h1 className="text-4xl font-bold">Task Manager</h1>
      </section>
      <ul className="flex-1 overflow-y-auto p-4">
        {userStoriesList.map((userStory) => (
          <li key={userStory.id} className="bg-white p-4 mb-4 rounded">
            <h2 className="text-2xl font-bold">{userStory.title}</h2>
            <p>{userStory.description}</p>
            <ul>
              {userStory.acceptance_criteria.map((acceptanceCriteria) => (
                <li key={acceptanceCriteria} className="ml-4">
                  {acceptanceCriteria}
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default App;