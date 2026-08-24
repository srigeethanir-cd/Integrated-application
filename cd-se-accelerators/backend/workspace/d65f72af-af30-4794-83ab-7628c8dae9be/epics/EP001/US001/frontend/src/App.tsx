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
];

const layoutRules: LayoutRule[] = [
  { id: 1, type: 'header', x: 0, y: 0, width: 360, height: 64 },
  { id: 2, type: 'hero_image', x: 0, y: 64, width: 360, height: 200 },
  { id: 3, type: 'button', x: 16, y: 300, width: 328, height: 48 },
  { id: 4, type: 'footer', x: 0, y: 400, width: 360, height: 64 },
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
    <div className="h-screen w-screen flex flex-col">
      <header className="h-16 bg-primary text-white p-4 flex justify-between">
        <h1 className="text-2xl font-bold">User Stories</h1>
        <button className="bg-secondary hover:bg-secondary-dark text-white font-bold py-2 px-4 rounded" onClick={() => handleUserStoryClick(userStories[0])}>
          View User Story
        </button>
      </header>
      <main className="flex-1 overflow-y-auto p-4">
        {userStory ? (
          <div className="bg-white p-4 rounded shadow-md">
            <h2 className="text-xl font-bold">{userStory.title}</h2>
            <p className="text-gray-600">{userStory.description}</p>
            <ul className="list-disc pl-4">
              {userStory.acceptance_criteria.map((criterion, index) => (
                <li key={index} className="py-2">
                  {criterion}
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <div className="bg-white p-4 rounded shadow-md">
            <h2 className="text-xl font-bold">Select a User Story</h2>
            <ul className="list-disc pl-4">
              {userStories.map((story, index) => (
                <li key={index} className="py-2" onClick={() => handleUserStoryClick(story)}>
                  {story.title}
                </li>
              ))}
            </ul>
          </div>
        )}
      </main>
      <footer className="h-16 bg-primary text-white p-4 flex justify-between">
        <p className="text-sm">&copy; 2024 User Stories</p>
        <button className="bg-secondary hover:bg-secondary-dark text-white font-bold py-2 px-4 rounded">
          Back to Top
        </button>
      </footer>
    </div>
  );
};

export default App;