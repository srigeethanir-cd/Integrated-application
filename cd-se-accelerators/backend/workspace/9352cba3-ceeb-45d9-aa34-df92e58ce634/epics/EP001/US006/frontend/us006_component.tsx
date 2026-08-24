typescript
// TaskComponent.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Task {
  id: number;
  title: string;
  completed: boolean;
}

const TaskComponent = () => {
  const [task, setTask] = useState<Task | null>(null);
  const [isCompleted, setIsCompleted] = useState(false);

  const taskId = 1; // Replace with actual task ID

  useEffect(() => {
    axios.get(`http://localhost:8000/tasks/${taskId}`)
      .then(response => {
        setTask(response.data);
        setIsCompleted(response.data.completed);
      })
      .catch(error => {
        console.error(error);
      });
  }, [taskId]);

  const handleMarkComplete = () => {
    axios.patch(`http://localhost:8000/tasks/${taskId}`, { completed: true })
      .then(response => {
        setTask(response.data);
        setIsCompleted(response.data.completed);
      })
      .catch(error => {
        console.error(error);
      });
  };

  if (!task) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h2>{task.title}</h2>
      <p>Completed: {isCompleted ? 'Yes' : 'No'}</p>
      <button onClick={handleMarkComplete}>Mark as Complete</button>
    </div>
  );
};

export default TaskComponent;