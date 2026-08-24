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
    small: string;
    medium: string;
    large: string;
  };
  corners: {
    small: string;
    medium: string;
    large: string;
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
  {
    id: 'US005',
    actor: 'User',
    title: 'Edit Task',
    epic_key: 'EP001',
    priority: 'Medium',
    story_key: 'US005',
    description: 'As a user, I want to update task information.',
    acceptance_criteria: ['Modify task title', 'Modify task status'],
  },
  {
    id: 'US006',
    actor: 'User',
    title: 'Mark Task Complete',
    epic_key: 'EP001',
    priority: 'Medium',
    story_key: 'US006',
    description: 'As a user, I want to mark a task as completed.',
    acceptance_criteria: ['Task status updates to completed'],
  },
  {
    id: 'US007',
    actor: 'User',
    title: 'Delete Task',
    epic_key: 'EP001',
    priority: 'Medium',
    story_key: 'US007',
    description: 'As a user, I want to delete tasks.',
    acceptance_criteria: ['Remove task from database'],
  },
  {
    id: 'US008',
    actor: 'User',
    title: 'Search Tasks',
    epic_key: 'EP001',
    priority: 'Low',
    story_key: 'US008',
    description: 'As a user, I want to search tasks by title.',
    acceptance_criteria: ['Search is case-insensitive', 'Filters list dynamically'],
  },
  {
    id: 'US009',
    actor: 'User',
    title: 'Filter Tasks',
    epic_key: 'EP001',
    priority: 'Low',
    story_key: 'US009',
    description: 'As a user, I want to filter tasks by status.',
    acceptance_criteria: ['Filter by completed or pending status'],
  },
  {
    id: 'US010',
    actor: 'User',
    title: 'Logout',
    epic_key: 'EP001',
    priority: 'High',
    story_key: 'US010',
    description: 'As a user, I want to securely log out.',
    acceptance_criteria: ['Invalidates session', 'Redirects to login page'],
  },
];

const layoutRules: LayoutRules = {
  type: 'mobile',
  orientation: 'portrait',
  grid_system: '12-column',
  sections: [
    {
      name: 'Navigation Bar',
      height: '56px',
      width: '100%',
      position: 'top',
    },
    {
      name: 'Hero Section',
      height: '200px',
      width: '100%',
      position: 'below Navigation Bar',
    },
    {
      name: 'Content Area',
      height: 'flex',
      width: '100%',
      position: 'below Hero Section',
    },
  ],
};

const colorsPalette: ColorsPalette = {
  primary_color: '#3498db',
  secondary_color: '#f1c40f',
  background_color: '#ffffff',
  text_color: '#333333',
};

const designTokens: DesignTokens = {
  spacing: {
    small: '8px',
    medium: '16px',
    large: '24px',
  },
  corners: {
    small: '4px',
    medium: '8px',
    large: '12px',
  },
};

const App: React.FC = () => {
  const [userStory, setUserStory] = useState<UserStory | null>(null);

  const handleUserStoryClick = (story: UserStory) => {
    setUserStory(story);
  };

  return (
    <div className="h-screen flex flex-col">
      <nav className="bg-primary_color text-white p-4 flex justify-between">
        <h1 className="text-2xl font-bold">Task Manager</h1>
        <button className="bg-secondary_color hover:bg-secondary_color-dark text-white font-bold py-2 px-4 rounded">
          Logout
        </button>
      </nav>
      <main className="flex-1 overflow-y-auto p-4">
        <section className="mb-4">
          <h2 className="text-xl font-bold mb-2">User Stories</h2>
          <ul>
            {userStories.map((story) => (
              <li key={story.id} className="mb-2">
                <button
                  className="bg-primary_color hover:bg-primary_color-dark text-white font-bold py-2 px-4 rounded"
                  onClick={() => handleUserStoryClick(story)}
                >
                  {story.title}
                </button>
              </li>
            ))}
          </ul>
        </section>
        {userStory && (
          <section>
            <h2 className="text-xl font-bold mb-2">{userStory.title}</h2>
            <p className="mb-2">{userStory.description}</p>
            <ul>
              {userStory.acceptance_criteria.map((criterion, index) => (
                <li key={index} className="mb-2">
                  {criterion}
                </li>
              ))}
            </ul>
          </section>
        )}
      </main>
    </div>
  );
};

export default App;