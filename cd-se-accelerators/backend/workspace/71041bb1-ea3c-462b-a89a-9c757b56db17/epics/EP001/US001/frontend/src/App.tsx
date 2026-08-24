import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

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

const UserStories: React.FC = () => {
  const [userStories, setUserStories] = useState<UserStory[]>([
    {"id": "US001", "actor": "User", "title": "User Registration", "epic_key": "EP001", "priority": "High", "story_key": "US001", "description": "As a new user, I want to register so I can manage tasks.", "acceptance_criteria": ["Register using name, email, password", "Email unique"]},
    {"id": "US002", "actor": "User", "title": "User Login", "epic_key": "EP001", "priority": "High", "story_key": "US002", "description": "As a user, I want to log in to access my dashboard.", "acceptance_criteria": ["Login with credentials", "Error on invalid credentials"]},
    {"id": "US003", "actor": "User", "title": "View Dashboard", "epic_key": "EP001", "priority": "Medium", "story_key": "US003", "description": "As a user, I want to see my tasks on a dashboard.", "acceptance_criteria": ["Display tasks list", "Show task count"]},
    {"id": "US004", "actor": "User", "title": "Create Task", "epic_key": "EP001", "priority": "High", "story_key": "US004", "description": "As a user, I want to create a task.", "acceptance_criteria": ["Enter task title", "Task is saved successfully"]},
    {"id": "US005", "actor": "User", "title": "Edit Task", "epic_key": "EP001", "priority": "Medium", "story_key": "US005", "description": "As a user, I want to update task information.", "acceptance_criteria": ["Modify task title", "Modify task status"]},
    {"id": "US006", "actor": "User", "title": "Mark Task Complete", "epic_key": "EP001", "priority": "Medium", "story_key": "US006", "description": "As a user, I want to mark a task as completed.", "acceptance_criteria": ["Task status updates to completed"]},
    {"id": "US007", "actor": "User", "title": "Delete Task", "epic_key": "EP001", "priority": "Medium", "story_key": "US007", "description": "As a user, I want to delete tasks.", "acceptance_criteria": ["Remove task from database"]},
    {"id": "US008", "actor": "User", "title": "Search Tasks", "epic_key": "EP001", "priority": "Low", "story_key": "US008", "description": "As a user, I want to search tasks by title.", "acceptance_criteria": ["Search is case-insensitive", "Filters list dynamically"]},
    {"id": "US009", "actor": "User", "title": "Filter Tasks", "epic_key": "EP001", "priority": "Low", "story_key": "US009", "description": "As a user, I want to filter tasks by status.", "acceptance_criteria": ["Filter by completed or pending status"]},
    {"id": "US010", "actor": "User", "title": "Logout", "epic_key": "EP001", "priority": "High", "story_key": "US010", "description": "As a user, I want to securely log out.", "acceptance_criteria": ["Invalidates session", "Redirects to login page"]},
  ]);

  const navigate = useNavigate();

  const handleRegister = () => {
    navigate('/register');
  };

  const handleLogin = () => {
    navigate('/login');
  };

  return (
    <div className="max-w-md mx-auto p-4 mt-12 bg-white rounded-lg shadow-md">
      <h2 className="text-lg font-bold mb-4">User Stories</h2>
      <ul>
        {userStories.map((story) => (
          <li key={story.id} className="mb-4">
            <h3 className="text-md font-bold">{story.title}</h3>
            <p>{story.description}</p>
            <ul>
              {story.acceptance_criteria.map((criterion) => (
                <li key={criterion} className="ml-4">{criterion}</li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
      <button className="bg-primary_color hover:bg-secondary_color text-white font-bold py-2 px-4 rounded" onClick={handleRegister}>
        Register
      </button>
      <button className="bg-primary_color hover:bg-secondary_color text-white font-bold py-2 px-4 rounded" onClick={handleLogin}>
        Login
      </button>
    </div>
  );
};

export default UserStories;