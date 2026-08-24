typescript
// TaskEditor.tsx
import React, { useState } from 'react';
import axios from 'axios';

interface Task {
  id: number;
  title: string;
  status: string;
}

interface TaskEditorProps {
  task: Task;
  onUpdateTask: (task: Task) => void;
}

const TaskEditor: React.FC<TaskEditorProps> = ({ task, onUpdateTask }) => {
  const [title, setTitle] = useState(task.title);
  const [status, setStatus] = useState(task.status);

  const handleTitleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setTitle(event.target.value);
  };

  const handleStatusChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setStatus(event.target.value);
  };

  const handleUpdateTask = async () => {
    try {
      const updatedTask: Task = {
        id: task.id,
        title,
        status,
      };

      const response = await axios.put(`http://localhost:8000/tasks/${task.id}`, updatedTask);
      onUpdateTask(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div>
      <label>
        Title:
        <input type="text" value={title} onChange={handleTitleChange} />
      </label>
      <br />
      <label>
        Status:
        <select value={status} onChange={handleStatusChange}>
          <option value="pending">Pending</option>
          <option value="in_progress">In Progress</option>
          <option value="done">Done</option>
        </select>
      </label>
      <br />
      <button onClick={handleUpdateTask}>Update Task</button>
    </div>
  );
};

export default TaskEditor;