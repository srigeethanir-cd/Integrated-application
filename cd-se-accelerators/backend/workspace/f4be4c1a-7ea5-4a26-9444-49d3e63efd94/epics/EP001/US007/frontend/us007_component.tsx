typescript
// TaskDeleteComponent.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Task {
  id: number;
  title: string;
}

interface Props {
  taskId: number;
  onDelete: () => void;
}

const TaskDeleteComponent: React.FC<Props> = ({ taskId, onDelete }) => {
  const [task, setTask] = useState<Task | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTask = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/tasks/${taskId}`);
        setTask(response.data);
      } catch (error) {
        setError(error.message);
      }
    };
    fetchTask();
  }, [taskId]);

  const handleDelete = async () => {
    try {
      await axios.delete(`http://localhost:8000/tasks/${taskId}`);
      onDelete();
    } catch (error) {
      setError(error.message);
    }
  };

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!task) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h2>Delete Task: {task.title}</h2>
      <button onClick={handleDelete}>Delete</button>
    </div>
  );
};

export default TaskDeleteComponent;