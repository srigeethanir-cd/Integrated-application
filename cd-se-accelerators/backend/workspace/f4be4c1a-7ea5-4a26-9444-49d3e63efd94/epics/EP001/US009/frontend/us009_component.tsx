typescript
// TaskFilter.tsx
import React, { useState } from 'react';

interface TaskFilterProps {
  onFilter: (status: string) => void;
}

const TaskFilter: React.FC<TaskFilterProps> = ({ onFilter }) => {
  const [status, setStatus] = useState('');

  const handleFilter = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedStatus = e.target.value;
    setStatus(selectedStatus);
    onFilter(selectedStatus);
  };

  return (
    <div>
      <select value={status} onChange={handleFilter}>
        <option value="">All</option>
        <option value="completed">Completed</option>
        <option value="pending">Pending</option>
      </select>
    </div>
  );
};

export default TaskFilter;