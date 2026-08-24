import React from 'react';
import CompleteTaskButton from './CompleteTaskButton';

export default function TaskItem({ task }: { task: any }) {
  return (
    <div className="flex items-center justify-between p-3 bg-white border rounded-lg shadow-sm">
      <div className="flex items-center gap-3">
        <CompleteTaskButton taskId={task.id} isCompleted={task.completed} />
        <span className={task.completed ? 'line-through text-slate-400' : 'font-medium text-slate-800'}>{task.title}</span>
      </div>
    </div>
  );
}
