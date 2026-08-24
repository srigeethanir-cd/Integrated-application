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
    { id: 3, type: "content", x: 0, y: 264, width: 375, height: 400 },
    { id: 4, type: "footer", x: 0, y: 664, width: 375, height: 56 }
  ]
};

const colorsPalette: ColorsPalette = {
  primary: "#3498db",
  secondary: "#f1c40f",
  background: "#ffffff",
  text: "#333333"
};

const designTokens: DesignTokens = {
  spacing: {
    small: 8,
    medium: 16,
    large: 24
  },
  corners: {
    small: 2,
    medium: 4,
    large: 8
  }
};

const CreateTask: React.FC = () => {
  const [taskTitle, setTaskTitle] = useState('');

  const handleCreateTask = () => {
    // Task creation logic goes here
    console.log('Task created successfully!');
  };

  return (
    <div className="h-screen flex flex-col">
      <header className="h-16 bg-primary text-white p-4 flex justify-center items-center">
        <h1 className="text-lg font-bold">Create Task</h1>
      </header>
      <main className="flex-1 p-4">
        <input
          type="text"
          value={taskTitle}
          onChange={(e) => setTaskTitle(e.target.value)}
          placeholder="Enter task title"
          className="w-full p-2 border border-gray-400 rounded-lg"
        />
        <button
          onClick={handleCreateTask}
          className="w-full p-2 bg-primary text-white rounded-lg mt-4"
        >
          Create Task
        </button>
      </main>
      <footer className="h-16 bg-secondary text-white p-4 flex justify-center items-center">
        <p className="text-sm font-bold">&copy; 2024</p>
      </footer>
    </div>
  );
};

export default CreateTask;