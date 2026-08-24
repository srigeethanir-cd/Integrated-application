import React, { useState } from 'react';

export default function TaskEditForm({ initialTask, onClose }: { initialTask: any; onClose: () => void }) {
  const [title, setTitle] = useState(initialTask?.title || '');
  const [description, setDescription] = useState(initialTask?.description || '');
  const [dueDate, setDueDate] = useState(initialTask?.due_date || '');

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Task Updated:', { title, description, dueDate });
    onClose();
  };

  return (
    <form onSubmit={handleSave} className="space-y-4">
      <input type="text" value={title} onChange={e => setTitle(e.target.value)} className="w-full p-2 border rounded" required />
      <textarea value={description} onChange={e => setDescription(e.target.value)} className="w-full p-2 border rounded" />
      <input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} className="w-full p-2 border rounded" />
      <div className="flex justify-end gap-2">
        <button type="button" onClick={onClose} className="px-4 py-2 border rounded">Cancel</button>
        <button type="submit" className="px-4 py-2 bg-amber-600 text-white rounded font-bold">Update</button>
      </div>
    </form>
  );
}
