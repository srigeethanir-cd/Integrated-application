typescript
// TaskSearchComponent.tsx
import React, { useState } from 'react';

interface Task {
  id: number;
  title: string;
}

interface TaskSearchComponentProps {
  tasks: Task[];
  onTaskSelected: (task: Task) => void;
}

const TaskSearchComponent: React.FC<TaskSearchComponentProps> = ({
  tasks,
  onTaskSelected,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredTasks, setFilteredTasks] = useState(tasks);

  const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
    const searchTerm = event.target.value.toLowerCase();
    setSearchTerm(searchTerm);
    const filteredTasks = tasks.filter((task) =>
      task.title.toLowerCase().includes(searchTerm)
    );
    setFilteredTasks(filteredTasks);
  };

  return (
    <div>
      <input
        type="search"
        value={searchTerm}
        onChange={handleSearch}
        placeholder="Search tasks"
      />
      <ul>
        {filteredTasks.map((task) => (
          <li key={task.id}>
            <button onClick={() => onTaskSelected(task)}>{task.title}</button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default TaskSearchComponent;