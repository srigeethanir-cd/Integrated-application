import React, { useState } from 'react';

export default function TaskForm({ onClose }: { onClose: () => void }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Task Created:', { title, description, dueDate });
    onClose();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <input type="text" placeholder="Task Title" value={title} onChange={e => setTitle(e.target.value)} className="w-full p-2 border rounded" required />
      <textarea placeholder="Description" value={description} onChange={e => setDescription(e.target.value)} className="w-full p-2 border rounded" />
      <input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} className="w-full p-2 border rounded" required />
      <div className="flex justify-end gap-2">
        <button type="button" onClick={onClose} className="px-4 py-2 border rounded">Cancel</button>
        <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded font-bold">Save Task</button>
      </div>
    </form>
  );
}
