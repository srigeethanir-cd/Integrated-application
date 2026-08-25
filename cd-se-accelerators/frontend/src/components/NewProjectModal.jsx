import React, { useState } from 'react';
import { FolderPlus, X, ArrowRight } from 'lucide-react';

export default function NewProjectModal({ isOpen, onClose, onProceed }) {
  const [projectName, setProjectName] = useState('');
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!projectName.trim()) {
      setError('Please enter a project name.');
      return;
    }
    setError('');
    onProceed(projectName.trim());
    setProjectName('');
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150">
      <div className="bg-white dark:bg-[#1B1E3A] border border-slate-200 dark:border-[#2B3674] rounded-2xl max-w-md w-full p-6 shadow-2xl relative overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-150 dark:border-[#2B3674]">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-[#FF5523]/10 text-[#FF5523] flex items-center justify-center font-bold">
              <FolderPlus className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-[#1B2559] dark:text-white">New Test Project</h3>
              <p className="text-xs text-[#707EAE] dark:text-[#A3AED0]">Define permanent identity for project testing</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <label className="block text-xs font-bold text-[#1B2559] dark:text-slate-200 mb-1.5 uppercase tracking-wide">
              Project Name <span className="text-[#FF5523]">*</span>
            </label>
            <input
              type="text"
              autoFocus
              value={projectName}
              onChange={(e) => {
                setProjectName(e.target.value);
                if (error) setError('');
              }}
              placeholder="e.g. React E-Commerce Login App"
              className="w-full bg-[#F4F7FE] dark:bg-[#11142D] border border-slate-250 dark:border-[#2B3674] rounded-xl px-4 py-2.5 text-xs text-[#1B2559] dark:text-white focus:outline-none focus:border-[#4318FF] transition-colors placeholder:text-slate-400"
            />
            {error && <p className="text-xs text-[#EE5D50] mt-1 font-medium">{error}</p>}
          </div>

          <div className="pt-2 flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-[#707EAE] dark:text-[#A3AED0] hover:text-[#1B2559] dark:hover:text-white bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 rounded-xl transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 text-xs font-semibold text-white bg-[#FF5523] hover:bg-[#E0481B] active:bg-[#C93B14] rounded-xl flex items-center gap-1.5 shadow-md shadow-[#FF5523]/25 transition-all transform hover:-translate-y-0.5 cursor-pointer"
            >
              <span>Proceed</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
