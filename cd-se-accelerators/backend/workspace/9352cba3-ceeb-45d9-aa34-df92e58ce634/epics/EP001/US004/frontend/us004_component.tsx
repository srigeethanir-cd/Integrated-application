typescript
// Task.ts
export interface Task {
  id: number;
  title: string;
}

// TaskForm.tsx
import React, { useState } from 'react';
import axios from 'axios';

const TaskForm = () => {
  const [title, setTitle] = useState('');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const response = await axios.post('/tasks', { title });
      if (response.status === 201) {
        setSuccess('Task is saved successfully');
        setTitle('');
      } else {
        setError('Failed to create task');
      }
    } catch (error) {
      setError('Failed to create task');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <label>
        Enter task title:
        <input type="text" value={title} onChange={(event) => setTitle(event.target.value)} />
      </label>
      <button type="submit">Create Task</button>
      {error && <div style={{ color: 'red' }}>{error}</div>}
      {success && <div style={{ color: 'green' }}>{success}</div>}
    </form>
  );
};

export default TaskForm;