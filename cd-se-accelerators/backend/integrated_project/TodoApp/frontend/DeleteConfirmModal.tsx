import React, { useState } from 'react';
import DeleteTaskButton from './DeleteTaskButton';

export default function DeleteConfirmModal({ taskId }: { taskId: string }) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div>
      <button onClick={() => setIsOpen(true)} className="text-red-600 font-bold hover:underline text-sm">Delete</button>
      {isOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white p-6 rounded-xl max-w-sm w-full space-y-4">
            <h3 className="text-lg font-bold text-red-600">Confirm Delete</h3>
            <p className="text-xs text-slate-600">Are you sure you want to delete this task? This action cannot be undone.</p>
            <div className="flex justify-end gap-2">
              <button onClick={() => setIsOpen(false)} className="px-3 py-1.5 border rounded">Cancel</button>
              <DeleteTaskButton taskId={taskId} onDeleted={() => setIsOpen(false)} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
