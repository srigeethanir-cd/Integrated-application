import React from 'react';

export default function DeleteTaskButton({ taskId, onDeleted }: { taskId: string; onDeleted: () => void }) {
  const handleDelete = () => {
    console.log('Deleting task:', taskId);
    onDeleted();
  };
  return (
    <button onClick={handleDelete} className="px-3 py-1.5 bg-red-600 text-white rounded font-bold">Delete</button>
  );
}
