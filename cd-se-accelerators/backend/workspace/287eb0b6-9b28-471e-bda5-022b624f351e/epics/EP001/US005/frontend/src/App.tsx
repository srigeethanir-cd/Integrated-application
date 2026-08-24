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
  id: "US005",
  actor: "User",
  title: "Edit Task",
  epic_key: "EP001",
  priority: "Medium",
  story_key: "US005",
  description: "As a user, I want to update task information.",
  acceptance_criteria: ["Modify task title", "Modify task status"]
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

const EditTask: React.FC = () => {
  const [taskTitle, setTaskTitle] = useState("");
  const [taskStatus, setTaskStatus] = useState("");

  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTaskTitle(e.target.value);
  };

  const handleStatusChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTaskStatus(e.target.value);
  };

  return (
    <div className="h-screen bg-white">
      <header className="h-16 bg-primary text-white flex justify-center items-center">
        <h1 className="text-2xl">{userStory.title}</h1>
      </header>
      <div className="h-50 bg-hero_image bg-cover bg-center">
        {/* Hero Image */}
      </div>
      <div className="mx-4 my-8">
        <input
          type="text"
          value={taskTitle}
          onChange={handleTitleChange}
          placeholder="Task Title"
          className="w-full p-2 border border-gray-400 rounded-md"
        />
        <input
          type="text"
          value={taskStatus}
          onChange={handleStatusChange}
          placeholder="Task Status"
          className="w-full p-2 border border-gray-400 rounded-md mt-4"
        />
        <button
          className="w-full p-2 bg-primary text-white rounded-md mt-4"
          onClick={() => console.log("Task updated successfully")}
        >
          Update Task
        </button>
      </div>
    </div>
  );
};

export default EditTask;