import React, { useState } from 'react';

export default function CompleteTaskButton({ taskId, isCompleted }: { taskId: string; isCompleted: boolean }) {
  const [done, setDone] = useState(isCompleted);
  return (
    <button onClick={() => setDone(!done)} className={`w-5 h-5 rounded border flex items-center justify-center ${done ? 'bg-emerald-500 text-white' : 'border-slate-300'}`}>
      {done && '✓'}
    </button>
  );
}
