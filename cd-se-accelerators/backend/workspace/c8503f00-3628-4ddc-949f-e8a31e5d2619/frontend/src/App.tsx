import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';

const App = () => {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  const handleRegister = (name: string, email: string, password: string) => {
    // Register user logic
    console.log('Register user:', name, email, password);
  };

  const handleLogin = (email: string, password: string) => {
    // Login user logic
    console.log('Login user:', email, password);
    setUser({ email, password });
  };

  const handleLogout = () => {
    // Logout user logic
    console.log('Logout user');
    setUser(null);
  };

  const handleCreateTask = (title: string) => {
    // Create task logic
    console.log('Create task:', title);
  };

  const handleEditTask = (id: number, title: string) => {
    // Edit task logic
    console.log('Edit task:', id, title);
  };

  const handleDeleteTask = (id: number) => {
    // Delete task logic
    console.log('Delete task:', id);
  };

  const handleSearchTasks = (query: string) => {
    // Search tasks logic
    console.log('Search tasks:', query);
  };

  const handleFilterTasks = (status: string) => {
    // Filter tasks logic
    console.log('Filter tasks:', status);
  };

  return (
    <div className="h-screen flex flex-col">
      <header className="h-16 bg-primary text-white p-4 flex justify-between">
        <h1 className="text-2xl font-bold">Task Manager</h1>
        {user ? (
          <button
            className="bg-secondary hover:bg-secondary-dark text-white font-bold py-2 px-4 rounded"
            onClick={handleLogout}
          >
            Logout
          </button>
        ) : (
          <NavLink
            to="/login"
            className="bg-secondary hover:bg-secondary-dark text-white font-bold py-2 px-4 rounded"
          >
            Login
          </NavLink>
        )}
      </header>
      <main className="flex-1 p-4">
        {user ? (
          <div className="flex flex-col">
            <h2 className="text-xl font-bold mb-4">Tasks</h2>
            <button
              className="bg-primary hover:bg-primary-dark text-white font-bold py-2 px-4 rounded mb-4"
              onClick={() => handleCreateTask('New Task')}
            >
              Create Task
            </button>
            <ul>
              {[1, 2, 3].map((id) => (
                <li key={id} className="mb-4">
                  <h3 className="text-lg font-bold">Task {id}</h3>
                  <button
                    className="bg-secondary hover:bg-secondary-dark text-white font-bold py-2 px-4 rounded mr-4"
                    onClick={() => handleEditTask(id, 'Edited Task')}
                  >
                    Edit
                  </button>
                  <button
                    className="bg-primary hover:bg-primary-dark text-white font-bold py-2 px-4 rounded"
                    onClick={() => handleDeleteTask(id)}
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
            <input
              type="search"
              placeholder="Search tasks"
              className="bg-gray-200 p-2 rounded mb-4"
              onChange={(e) => handleSearchTasks(e.target.value)}
            />
            <select
              className="bg-gray-200 p-2 rounded mb-4"
              onChange={(e) => handleFilterTasks(e.target.value)}
            >
              <option value="">All</option>
              <option value="completed">Completed</option>
              <option value="pending">Pending</option>
            </select>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full">
            <h2 className="text-xl font-bold mb-4">Please login to access tasks</h2>
            <NavLink
              to="/login"
              className="bg-secondary hover:bg-secondary-dark text-white font-bold py-2 px-4 rounded"
            >
              Login
            </NavLink>
          </div>
        )}
      </main>
      <footer className="h-10 bg-primary text-white p-4 flex justify-between">
        <p>&copy; 2024 Task Manager</p>
      </footer>
    </div>
  );
};

export default App;