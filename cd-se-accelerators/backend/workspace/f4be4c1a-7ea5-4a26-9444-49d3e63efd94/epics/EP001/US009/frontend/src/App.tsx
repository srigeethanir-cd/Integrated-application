import React, { useState } from 'react';

interface Task {
  id: string;
  status: 'completed' | 'pending';
}

interface UserStory {
  id: string;
  actor: string;
  title: string;
  epic_key: string;
  priority: string;
  story_key: string;
  description: string;
  acceptance_criteria: string[];
}

const UserStoryComponent: React.FC<{ userStory: UserStory; tasks: Task[] }> = ({
  userStory,
  tasks,
}) => {
  const [filterStatus, setFilterStatus] = useState<'completed' | 'pending' | 'all'>('all');

  const filteredTasks = tasks.filter((task) => {
    if (filterStatus === 'all') return true;
    return task.status === filterStatus;
  });

  return (
    <div className="max-w-md mx-auto p-4 bg-background rounded-lg shadow-md">
      <h2 className="text-primary text-lg font-bold mb-2">{userStory.title}</h2>
      <p className="text-gray-500 mb-4">{userStory.description}</p>
      <div className="flex gap-2 mb-4">
        <button
          className={`py-2 px-4 rounded-lg ${filterStatus === 'all' ? 'bg-primary text-white' : 'bg-gray-200 text-gray-500'}`}
          onClick={() => setFilterStatus('all')}
        >
          All
        </button>
        <button
          className={`py-2 px-4 rounded-lg ${filterStatus === 'completed' ? 'bg-primary text-white' : 'bg-gray-200 text-gray-500'}`}
          onClick={() => setFilterStatus('completed')}
        >
          Completed
        </button>
        <button
          className={`py-2 px-4 rounded-lg ${filterStatus === 'pending' ? 'bg-primary text-white' : 'bg-gray-200 text-gray-500'}`}
          onClick={() => setFilterStatus('pending')}
        >
          Pending
        </button>
      </div>
      <ul>
        {filteredTasks.map((task) => (
          <li key={task.id} className="py-2 border-b border-gray-200">
            <span className={`text-gray-500 ${task.status === 'completed' ? 'line-through' : ''}`}>{task.id}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default UserStoryComponent;