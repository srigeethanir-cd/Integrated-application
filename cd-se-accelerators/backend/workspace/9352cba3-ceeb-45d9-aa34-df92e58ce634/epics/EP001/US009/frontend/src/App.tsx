import React, { useState } from 'react';

interface Task {
  id: string;
  status: 'completed' | 'pending';
}

const TaskFilter: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([
    { id: '1', status: 'pending' },
    { id: '2', status: 'completed' },
    { id: '3', status: 'pending' },
  ]);
  const [filter, setFilter] = useState<'all' | 'completed' | 'pending'>('all');

  const handleFilterChange = (newFilter: 'all' | 'completed' | 'pending') => {
    setFilter(newFilter);
  };

  const filteredTasks = tasks.filter((task) => {
    if (filter === 'all') return true;
    return task.status === filter;
  });

  return (
    <div className="h-screen flex flex-col">
      <header className="h-14 bg-primary text-white flex justify-center items-center">
        Task Filter
      </header>
      <main className="flex-1 p-4">
        <div className="mb-4">
          <button
            className={`mr-2 ${filter === 'all' ? 'bg-primary text-white' : 'bg-white text-primary'} px-4 py-2 rounded`}
            onClick={() => handleFilterChange('all')}
          >
            All
          </button>
          <button
            className={`mr-2 ${filter === 'completed' ? 'bg-primary text-white' : 'bg-white text-primary'} px-4 py-2 rounded`}
            onClick={() => handleFilterChange('completed')}
          >
            Completed
          </button>
          <button
            className={`${filter === 'pending' ? 'bg-primary text-white' : 'bg-white text-primary'} px-4 py-2 rounded`}
            onClick={() => handleFilterChange('pending')}
          >
            Pending
          </button>
        </div>
        <ul>
          {filteredTasks.map((task) => (
            <li key={task.id} className="mb-2">
              <span
                className={`px-4 py-2 rounded ${task.status === 'completed' ? 'bg-green-200 text-green-600' : 'bg-yellow-200 text-yellow-600'}`}
              >
                {task.id} - {task.status}
              </span>
            </li>
          ))}
        </ul>
      </main>
      <footer className="h-14 bg-primary text-white flex justify-center items-center">
        Footer
      </footer>
    </div>
  );
};

export default TaskFilter;