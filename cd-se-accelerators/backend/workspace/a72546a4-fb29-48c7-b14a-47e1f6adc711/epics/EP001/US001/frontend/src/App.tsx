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
    description: 'As a new user, I want to register an account so that I can access the application.',
    acceptance_criteria: [
      'User can register using name, email, and password',
      'Email address must be unique',
      'Password must meet the required security rules',
      'Successful registration creates a user account',
    ],
  },
  {
    id: 'US002',
    actor: 'User',
    title: 'User Login',
    epic_key: 'EP001',
    priority: 'High',
    story_key: 'US002',
    description: 'As a registered user, I want to log in using my credentials so that I can access my account.',
    acceptance_criteria: [
      'User can log in using a registered email and password',
      'Valid credentials allow access to the dashboard',
      'Invalid credentials display an appropriate error message',
      'Login session is created successfully after authentication',
    ],
  },
  {
    id: 'US003',
    actor: 'User',
    title: 'View Dashboard',
    epic_key: 'EP001',
    priority: 'Medium',
    story_key: 'US003',
    description: 'As a user, I want to view my dashboard so that I can see an overview of my tasks.',
    acceptance_criteria: [
      'Dashboard displays the user\'s tasks',
      'Dashboard shows the total number of tasks',
      'Only tasks belonging to the logged-in user are displayed',
      'Dashboard loads successfully after login',
    ],
  },
  {
    id: 'US004',
    actor: 'User',
    title: 'Create Task',
    epic_key: 'EP001',
    priority: 'High',
    story_key: 'US004',
    description: 'As a user, I want to create a new task so that I can track work that needs to be completed.',
    acceptance_criteria: [
      'User can enter a task title',
      'User can submit the task successfully',
      'Created task is stored in the database',
      'New task appears in the user\'s task list',
    ],
  },
  {
    id: 'US005',
    actor: 'User',
    title: 'Edit Task',
    epic_key: 'EP001',
    priority: 'Medium',
    story_key: 'US005',
    description: 'As a user, I want to edit my task information so that I can keep task details up to date.',
    acceptance_criteria: [
      'User can select an existing task for editing',
      'User can modify the task title',
      'User can modify the task status',
      'Updated task information is saved in the database',
      'Updated information is immediately reflected in the task list',
    ],
  },
];

const layoutRules: LayoutRule[] = [
  { id: 1, type: 'header', x: 0, y: 0, width: 360, height: 64 },
  { id: 2, type: 'hero_image', x: 0, y: 64, width: 360, height: 200 },
  { id: 3, type: 'text_block', x: 16, y: 264, width: 328, height: 120 },
  { id: 4, type: 'call_to_action', x: 16, y: 384, width: 328, height: 48 },
];

const colorsPalette: ColorsPalette = {
  primary: '#3498db',
  secondary: '#f1c40f',
  background: '#f9f9f9',
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
    <div className="h-screen w-screen flex flex-col items-center justify-center">
      <header className="w-full h-64 bg-primary text-white flex justify-center items-center">
        <h1 className="text-3xl font-bold">User Stories</h1>
      </header>
      <main className="w-full h-full flex flex-col items-center justify-center">
        {userStories.map((story) => (
          <div
            key={story.id}
            className="w-328 h-120 bg-white shadow-md rounded-md p-4 m-4 flex flex-col items-center justify-center"
            onClick={() => handleUserStoryClick(story)}
          >
            <h2 className="text-xl font-bold">{story.title}</h2>
            <p className="text-lg">{story.description}</p>
          </div>
        ))}
      </main>
      {userStory && (
        <div className="fixed bottom-0 left-0 w-full h-48 bg-primary text-white flex justify-center items-center">
          <h2 className="text-xl font-bold">{userStory.title}</h2>
          <ul className="list-disc pl-4">
            {userStory.acceptance_criteria.map((criterion) => (
              <li key={criterion} className="text-lg">
                {criterion}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default App;