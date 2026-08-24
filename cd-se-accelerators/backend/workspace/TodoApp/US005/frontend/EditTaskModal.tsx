import React, { useState } from 'react';
import TaskEditForm from './TaskEditForm';

export default function EditTaskModal({ task }: { task: any }) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div>
      <button onClick={() => setIsOpen(true)} className="text-sm text-amber-600 font-bold hover:underline">Edit</button>
      {isOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white p-6 rounded-xl max-w-md w-full">
            <h3 className="text-xl font-bold mb-4">Edit Task</h3>
            <TaskEditForm initialTask={task} onClose={() => setIsOpen(false)} />
          </div>
        </div>
      )}
    </div>
  );
}
