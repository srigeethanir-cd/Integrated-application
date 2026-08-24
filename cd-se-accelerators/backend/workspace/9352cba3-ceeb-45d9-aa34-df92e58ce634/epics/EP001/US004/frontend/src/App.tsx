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
    { id: 2, type: "hero_image", x: 0, y: 64, width: 375, height: 200 },
    { id: 3, type: "text_block", x: 16, y: 264, width: 343, height: 100 },
    { id: 4, type: "call_to_action", x: 16, y: 364, width: 343, height: 50 }
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
    <div className="h-screen bg-white">
      <header className="h-16 bg-primary text-white flex justify-center items-center">
        <h1 className="text-2xl">{userStory.title}</h1>
      </header>
      <div className="h-50 bg-hero-image bg-cover bg-center">
        {/* Hero image goes here */}
      </div>
      <div className="mx-4 my-8">
        <input
          type="text"
          placeholder="Enter task title"
          value={taskTitle}
          onChange={(e) => setTaskTitle(e.target.value)}
          className="w-full p-2 pl-10 text-sm text-gray-700 border border-gray-200 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
        />
        <button
          onClick={handleCreateTask}
          className="w-full p-2 mt-4 text-white bg-primary rounded-md hover:bg-secondary"
        >
          Create Task
        </button>
      </div>
    </div>
  );
};

export default CreateTask;