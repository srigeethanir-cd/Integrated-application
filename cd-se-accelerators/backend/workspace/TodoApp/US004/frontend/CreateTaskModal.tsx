import React, { useState } from 'react';
import TaskForm from './TaskForm';

export default function CreateTaskModal() {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div>
      <button onClick={() => setIsOpen(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg font-bold">+ Add Task</button>
      {isOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white p-6 rounded-xl max-w-md w-full">
            <h3 className="text-xl font-bold mb-4">Create New Task</h3>
            <TaskForm onClose={() => setIsOpen(false)} />
          </div>
        </div>
      )}
    </div>
  );
}
