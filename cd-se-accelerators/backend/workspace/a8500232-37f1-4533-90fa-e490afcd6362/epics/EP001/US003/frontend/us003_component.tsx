typescript
// Task.ts
export interface Task {
  id: number;
  title: string;
  description: string;
}

// TaskList.tsx
import React from 'react';
import { Task } from './Task';

interface TaskListProps {
  tasks: Task[];
}

const TaskList: React.FC<TaskListProps> = ({ tasks }) => {
  return (
    <ul>
      {tasks.map((task) => (
        <li key={task.id}>
          <h2>{task.title}</h2>
          <p>{task.description}</p>
        </li>
      ))}
    </ul>
  );
};

export default TaskList;

// Dashboard.tsx
import React, { useState, useEffect } from 'react';
import TaskList from './TaskList';
import { Task } from './Task';

const Dashboard = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskCount, setTaskCount] = useState(0);

  useEffect(() => {
    const fetchTasks = async () => {
      const response = await fetch('http://localhost:8000/tasks');
      const data = await response.json();
      setTasks(data);
      setTaskCount(data.length);
    };
    fetchTasks();
  }, []);

  return (
    <div>
      <h1>Dashboard</h1>
      <p>Task Count: {taskCount}</p>
      <TaskList tasks={tasks} />
    </div>
  );
};

export default Dashboard;