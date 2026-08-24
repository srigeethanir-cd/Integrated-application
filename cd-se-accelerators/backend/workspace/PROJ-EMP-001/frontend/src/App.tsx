import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const App = () => {
  const [userStory, setUserStory] = useState([
    {"id": "US001", "title": "User Registration", "description": "As a new user, I want to create an account so that I can manage my personal tasks.", "priority": "High", "actor": "User", "acceptance_criteria": ["User can register using name, email, and password.", "Email must be unique.", "Password must contain at least 8 characters.", "Successful registration redirects to the login page."]},
    {"id": "US002", "title": "User Login", "description": "As a registered user, I want to log into the application so that I can access my tasks.", "priority": "High", "actor": "User", "acceptance_criteria": ["User can log in using valid credentials.", "Invalid credentials display an error.", "Successful login redirects to the dashboard."]},
    {"id": "US003", "title": "View Dashboard", "description": "As a logged-in user, I want to view my dashboard so that I can see all my tasks.", "priority": "Medium", "actor": "User", "acceptance_criteria": ["Dashboard displays all tasks.", "Completed tasks are shown separately.", "Pending tasks are shown separately.", "Task count is displayed."]},
    {"id": "US004", "title": "Create Task", "description": "As a user, I want to create a new task so that I can organize my work.", "priority": "High", "actor": "User", "acceptance_criteria": ["User can enter task title.", "User can enter task description.", "User can set a due date.", "Task is saved successfully."]},
    {"id": "US005", "title": "Edit Task", "description": "As a user, I want to edit an existing task so that I can keep my task information updated.", "priority": "Medium", "actor": "User", "acceptance_criteria": ["User can edit task title.", "User can edit task description.", "User can update due date.", "Changes are saved successfully."]},
    {"id": "US006", "title": "Mark Task as Completed", "description": "As a user, I want to mark a task as completed so that I know it has been finished.", "priority": "Medium", "actor": "User", "acceptance_criteria": ["Completed tasks display a completed badge.", "Completed tasks move to the completed section.", "Completion status is stored."]},
    {"id": "US007", "title": "Delete Task", "description": "As a user, I want to delete unnecessary tasks so that my task list stays clean.", "priority": "Medium", "actor": "User", "acceptance_criteria": ["User can delete a task.", "Confirmation dialog is displayed.", "Deleted task is removed permanently."]},
    {"id": "US008", "title": "Search Tasks", "description": "As a user, I want to search tasks by title so that I can quickly find specific tasks.", "priority": "Low", "actor": "User", "acceptance_criteria": ["Search filters tasks by title.", "Search is case-insensitive.", "Clearing the search displays all tasks."]},
    {"id": "US009", "title": "Filter Tasks", "description": "As a user, I want to filter tasks based on their status so that I can focus on relevant work.", "priority": "Low", "actor": "User", "acceptance_criteria": ["Filter by All.", "Filter by Pending.", "Filter by Completed."]},
    {"id": "US010", "title": "User Logout", "description": "As a user, I want to securely log out of the application so that my account remains protected.", "priority": "Medium", "actor": "User", "acceptance_criteria": ["User session is cleared.", "User is redirected to the login page.", "Protected pages cannot be accessed after logout."]}
  ]);

  const [layout, setLayout] = useState({
    "type": "mobile",
    "orientation": "portrait",
    "components": [
      {"id": 1, "type": "header", "x": 0, "y": 0, "width": 360, "height": 64},
      {"id": 2, "type": "hero_image", "x": 0, "y": 64, "width": 360, "height": 200},
      {"id": 3, "type": "text_block", "x": 16, "y": 264, "width": 328, "height": 100},
      {"id": 4, "type": "call_to_action", "x": 16, "y": 364, "width": 328, "height": 44}
    ]
  });

  const [colors, setColors] = useState({
    "primary": "#3498db",
    "secondary": "#f1c40f",
    "background": "#ffffff",
    "text": "#333333"
  });

  const [designTokens, setDesignTokens] = useState({
    "spacing": {"small": 8, "medium": 16, "large": 24},
    "corners": {"small": 2, "medium": 4, "large": 8}
  });

  return (
    <div className="h-screen w-screen flex flex-col items-center justify-center">
      <header className="h-16 w-full bg-primary text-white flex justify-center items-center">
        <h1 className="text-2xl font-bold">Task Management App</h1>
      </header>
      <main className="h-full w-full flex flex-col items-center justify-center">
        <div className="h-64 w-full bg-hero_image bg-cover bg-center flex justify-center items-center">
          <h2 className="text-3xl font-bold text-white">Get Started</h2>
        </div>
        <div className="h-100 w-full p-4 flex flex-col items-center justify-center">
          <p className="text-lg font-medium text-text">Create an account to manage your tasks</p>
          <button className="h-12 w-48 bg-primary text-white font-medium rounded-lg hover:bg-secondary">Register</button>
        </div>
        <div className="h-12 w-full bg-primary text-white flex justify-center items-center">
          <p className="text-sm font-medium">Already have an account? <Link to="/login" className="text-white hover:text-secondary">Login</Link></p>
        </div>
      </main>
    </div>
  );
};

export default App;