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
    { id: 3, type: "title", x: 16, y: 264, width: 343, height: 24 },
    { id: 4, type: "description", x: 16, y: 288, width: 343, height: 48 },
    { id: 5, type: "call_to_action", x: 16, y: 336, width: 343, height: 44 }
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
  const [title, setTitle] = useState(userStory.title);
  const [description, setDescription] = useState(userStory.description);

  const handleTitleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setTitle(event.target.value);
  };

  const handleDescriptionChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setDescription(event.target.value);
  };

  return (
    <div className="h-screen bg-white">
      <header className="bg-primary h-16 flex justify-center items-center text-white">
        <h1 className="text-lg font-bold">Edit Task</h1>
      </header>
      <div className="hero-image h-48 bg-secondary flex justify-center items-center">
        <h2 className="text-lg font-bold text-white">Hero Image</h2>
      </div>
      <div className="title mt-4 ml-4">
        <input
          type="text"
          value={title}
          onChange={handleTitleChange}
          className="w-full p-2 border border-gray-400 rounded"
          placeholder="Task Title"
        />
      </div>
      <div className="description mt-4 ml-4">
        <input
          type="text"
          value={description}
          onChange={handleDescriptionChange}
          className="w-full p-2 border border-gray-400 rounded"
          placeholder="Task Description"
        />
      </div>
      <div className="call-to-action mt-4 ml-4">
        <button
          className="bg-primary text-white p-2 rounded"
          onClick={() => console.log("Task updated successfully")}
        >
          Update Task
        </button>
      </div>
    </div>
  );
};

export default EditTask;