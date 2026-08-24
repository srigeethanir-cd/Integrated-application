import React, { useState } from 'react';

interface UserStory {
  id: string;
  actor: string;
  title: string;
  priority: string;
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
  { id: 'US001', actor: 'User', title: 'User Registration', priority: 'High', description: 'As a new user, I want to register so I can manage tasks.', acceptance_criteria: ['Register using name, email, password', 'Email unique'] },
  { id: 'US002', actor: 'User', title: 'User Login', priority: 'High', description: 'As a user, I want to log in to access my dashboard.', acceptance_criteria: ['Login with credentials', 'Error on invalid credentials'] },
  { id: 'US003', actor: 'User', title: 'View Dashboard', priority: 'Medium', description: 'As a user, I want to see my tasks on a dashboard.', acceptance_criteria: ['Display tasks list', 'Show task count'] },
  { id: 'US004', actor: 'User', title: 'Create Task', priority: 'High', description: 'As a user, I want to create a task.', acceptance_criteria: ['Enter task title', 'Task is saved successfully'] },
  { id: 'US005', actor: 'User', title: 'Edit Task', priority: 'Medium', description: 'As a user, I want to update task information.', acceptance_criteria: ['Modify task title', 'Modify task status'] },
  { id: 'US006', actor: 'User', title: 'Mark Task Complete', priority: 'Medium', description: 'As a user, I want to mark a task as completed.', acceptance_criteria: ['Task status updates to completed'] },
  { id: 'US007', actor: 'User', title: 'Delete Task', priority: 'Medium', description: 'As a user, I want to delete tasks.', acceptance_criteria: ['Remove task from database'] },
  { id: 'US008', actor: 'User', title: 'Search Tasks', priority: 'Low', description: 'As a user, I want to search tasks by title.', acceptance_criteria: ['Search is case-insensitive', 'Filters list dynamically'] },
  { id: 'US009', actor: 'User', title: 'Filter Tasks', priority: 'Low', description: 'As a user, I want to filter tasks by status.', acceptance_criteria: ['Filter by completed or pending status'] },
  { id: 'US010', actor: 'User', title: 'Logout', priority: 'High', description: 'As a user, I want to securely log out.', acceptance_criteria: ['Invalidates session', 'Redirects to login page'] },
];

const layoutRules: LayoutRule[] = [
  { id: 1, type: 'header', x: 0, y: 0, width: 375, height: 64 },
  { id: 2, type: 'hero_image', x: 0, y: 64, width: 375, height: 200 },
  { id: 3, type: 'title', x: 16, y: 264, width: 343, height: 24 },
  { id: 4, type: 'description', x: 16, y: 288, width: 343, height: 48 },
  { id: 5, type: 'call_to_action', x: 16, y: 336, width: 343, height: 48 },
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

const App = () => {
  const [userStory, setUserStory] = useState<UserStory | null>(null);

  const handleUserStoryClick = (story: UserStory) => {
    setUserStory(story);
  };

  return (
    <div className="h-screen w-screen flex flex-col items-center justify-center">
      <header className="w-full h-64 bg-primary text-white flex justify-center items-center">
        <h1 className="text-3xl font-bold">User Stories</h1>
      </header>
      <main className="w-full h-full flex flex-col items-center justify-center">
        <div className="w-11/12 h-5/6 overflow-y-scroll">
          {userStories.map((story) => (
            <div key={story.id} className="w-full h-24 bg-white shadow-md mb-4 flex justify-center items-center" onClick={() => handleUserStoryClick(story)}>
              <h2 className="text-lg font-bold">{story.title}</h2>
            </div>
          ))}
        </div>
        {userStory && (
          <div className="w-11/12 h-5/6 bg-white shadow-md mt-4 p-4">
            <h2 className="text-lg font-bold">{userStory.title}</h2>
            <p className="text-sm">{userStory.description}</p>
            <ul>
              {userStory.acceptance_criteria.map((criterion) => (
                <li key={criterion} className="text-sm">{criterion}</li>
              ))}
            </ul>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;