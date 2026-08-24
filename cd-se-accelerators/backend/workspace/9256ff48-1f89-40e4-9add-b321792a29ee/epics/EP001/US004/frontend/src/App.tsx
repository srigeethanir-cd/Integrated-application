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
    { id: 1, type: "header", x: 0, y: 0, width: 360, height: 64 },
    { id: 2, type: "hero_image", x: 0, y: 64, width: 360, height: 200 },
    { id: 3, type: "button", x: 100, y: 300, width: 160, height: 40 },
    { id: 4, type: "footer", x: 0, y: 440, width: 360, height: 40 }
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
    console.log(`Task "${taskTitle}" created successfully!`);
  };

  return (
    <div className="h-screen w-screen bg-white flex flex-col">
      <header className="h-16 w-full bg-primary text-white flex justify-center items-center">
        {layoutRules.components[0].type}
      </header>
      <div className="h-48 w-full bg-secondary flex justify-center items-center">
        {layoutRules.components[1].type}
      </div>
      <input
        type="text"
        value={taskTitle}
        onChange={(e) => setTaskTitle(e.target.value)}
        placeholder="Enter task title"
        className="w-64 h-10 p-2 mx-auto mt-10 border border-gray-300 rounded"
      />
      <button
        onClick={handleCreateTask}
        className="w-64 h-10 bg-primary text-white rounded mx-auto mt-4"
      >
        Create Task
      </button>
      <footer className="h-10 w-full bg-primary text-white flex justify-center items-center absolute bottom-0">
        {layoutRules.components[3].type}
      </footer>
    </div>
  );
};

export default CreateTask;