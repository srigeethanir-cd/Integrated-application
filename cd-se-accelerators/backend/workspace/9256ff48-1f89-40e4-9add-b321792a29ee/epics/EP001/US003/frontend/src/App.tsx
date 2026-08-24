import React from 'react';

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
    padding: string;
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

const userStory: UserStory = {
  id: "US003",
  actor: "User",
  title: "View Dashboard",
  epic_key: "EP001",
  priority: "Medium",
  story_key: "US003",
  description: "As a user, I want to see my tasks on a dashboard.",
  acceptance_criteria: ["Display tasks list", "Show task count"]
};

const layoutRules: LayoutRules = {
  type: "mobile",
  orientation: "portrait",
  grid_system: "12-column",
  sections: [
    { name: "header", height: "56px", padding: "16px" },
    { name: "search_bar", height: "48px", padding: "8px" },
    { name: "navigation_menu", height: "64px", padding: "16px" },
    { name: "content_area", height: "flexible", padding: "24px" },
    { name: "call_to_action_button", height: "48px", padding: "16px" }
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
    small: "8px",
    medium: "16px",
    large: "24px"
  },
  corners: {
    small: "2px",
    medium: "4px",
    large: "8px"
  }
};

const Dashboard: React.FC = () => {
  return (
    <div className="h-screen flex flex-col">
      {/* Header Section */}
      <div className="h-14 p-4 bg-primary text-white">
        <h1 className="text-lg font-bold">Dashboard</h1>
      </div>

      {/* Search Bar Section */}
      <div className="h-12 p-2 bg-background">
        <input type="search" placeholder="Search tasks" className="w-full p-2 pl-10 text-sm text-gray-700" />
      </div>

      {/* Navigation Menu Section */}
      <div className="h-16 p-4 bg-background">
        <ul className="flex justify-between">
          <li className="mr-4">
            <a href="#" className="text-sm text-gray-700 hover:text-primary">Tasks</a>
          </li>
          <li className="mr-4">
            <a href="#" className="text-sm text-gray-700 hover:text-primary">Settings</a>
          </li>
        </ul>
      </div>

      {/* Content Area Section */}
      <div className="flex-1 p-6 bg-background">
        <h2 className="text-lg font-bold mb-4">Tasks</h2>
        <ul>
          <li className="mb-4">
            <div className="bg-white p-4 rounded-lg shadow-md">
              <h3 className="text-sm font-bold mb-2">Task 1</h3>
              <p className="text-sm text-gray-700">This is a sample task.</p>
            </div>
          </li>
          <li className="mb-4">
            <div className="bg-white p-4 rounded-lg shadow-md">
              <h3 className="text-sm font-bold mb-2">Task 2</h3>
              <p className="text-sm text-gray-700">This is another sample task.</p>
            </div>
          </li>
        </ul>
      </div>

      {/* Call to Action Button Section */}
      <div className="h-12 p-4 bg-primary text-white">
        <button className="w-full p-2 text-sm font-bold">Create New Task</button>
      </div>
    </div>
  );
};

export default Dashboard;