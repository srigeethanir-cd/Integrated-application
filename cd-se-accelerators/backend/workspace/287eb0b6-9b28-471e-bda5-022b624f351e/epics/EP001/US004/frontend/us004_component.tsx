typescript
// CreateTaskComponent.tsx
import React, { useState } from 'react';
import axios from 'axios';

interface CreateTaskProps {
  // Add props if needed
}

const CreateTaskComponent: React.FC<CreateTaskProps> = () => {
  const [taskTitle, setTaskTitle] = useState('');
  const [isTaskSaved, setIsTaskSaved] = useState(false);

  const handleTaskTitleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setTaskTitle(event.target.value);
  };

  const handleCreateTask = async () => {
    try {
      const response = await axios.post('/tasks', { title: taskTitle });
      if (response.status === 201) {
        setIsTaskSaved(true);
      }
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div>
      <input
        type="text"
        value={taskTitle}
        onChange={handleTaskTitleChange}
        placeholder="Enter task title"
      />
      <button onClick={handleCreateTask}>Create Task</button>
      {isTaskSaved && <p>Task is saved successfully</p>}
    </div>
  );
};

export default CreateTaskComponent;