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
  components: {
    id: number;
    type: string;
    x: number;
    y: number;
    width: number;
    height: number;
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

const userStory: UserStory = {
  id: "US004",
  actor: "User",
  title: "Create Task",
  epic_key: "EP001",
  priority: "High",
  story_key: "US004",
  description: "As a user, I want to create a task.",
  acceptance_criteria: ["Enter task title", "Task is saved successfully"]
};

const layoutRules: LayoutRules = {
  type: "mobile",
  orientation: "portrait",
  components: [
    { id: 1, type: "header", x: 0, y: 0, width: 375, height: 64 },
    { id: 2, type: "hero", x: 0, y: 64, width: 375, height: 200 },
    { id: 3, type: "button", x: 100, y: 300, width: 175, height: 50 },
    { id: 4, type: "footer", x: 0, y: 500, width: 375, height: 50 }
  ]
};

const colorsPalette: ColorsPalette = {
  primary: "#3498db",
  secondary: "#f1c40f",
  background: "#f9f9f9",
  text: "#333333"
};

const designTokens: DesignTokens = {
  spacing: {
    small: 8,
    medium: 16,
    large: 24
  },
  corners: {
    small: 4,
    medium: 8,
    large: 12
  }
};

const CreateTask: React.FC = () => {
  const [taskTitle, setTaskTitle] = useState('');

  const handleCreateTask = () => {
    // Task creation logic goes here
    console.log('Task created successfully!');
  };

  return (
    <div className="h-screen bg-background">
      <header className="h-64 bg-primary text-text p-4 flex justify-center items-center">
        <h1 className="text-3xl font-bold">{userStory.title}</h1>
      </header>
      <main className="h-200 bg-hero p-4 flex justify-center items-center">
        <input
          type="text"
          value={taskTitle}
          onChange={(e) => setTaskTitle(e.target.value)}
          placeholder="Enter task title"
          className="w-full p-2 pl-10 text-text border border-secondary rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary"
        />
      </main>
      <button
        onClick={handleCreateTask}
        className="bg-primary text-text p-2 pl-5 pr-5 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary"
      >
        Create Task
      </button>
      <footer className="h-50 bg-primary text-text p-4 flex justify-center items-center">
        <p>&copy; 2024 Create Task App</p>
      </footer>
    </div>
  );
};

export default CreateTask;