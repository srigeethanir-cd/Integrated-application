typescript
// TaskDashboard.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Task {
  id: number;
  title: string;
  description: string;
}

const TaskDashboard: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskCount, setTaskCount] = useState(0);

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const response = await axios.get('http://localhost:8000/tasks');
        setTasks(response.data);
        setTaskCount(response.data.length);
      } catch (error) {
        console.error(error);
      }
    };
    fetchTasks();
  }, []);

  return (
    <div>
      <h1>Task Dashboard</h1>
      <p>Task Count: {taskCount}</p>
      <ul>
        {tasks.map((task) => (
          <li key={task.id}>
            <h2>{task.title}</h2>
            <p>{task.description}</p>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default TaskDashboard;