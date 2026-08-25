import React from 'react';
import {
  LayoutDashboard,
  FolderGit2,
  ClipboardList,
  FileText,
  BarChart3,
  Sun,
  Moon,
  Code2
} from 'lucide-react';

export default function Sidebar({
  activeTab,
  setActiveTab,
  darkMode,
  setDarkMode,
  onNewRun,
  testCaseCount = 0,
  testCasesLoading = false,
}) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'projects', label: 'Projects', icon: FolderGit2 },
    {
      id: 'test-cases',
      label: 'Test Cases',
      icon: ClipboardList,
      badge: testCasesLoading
        ? 'loading'
        : testCaseCount > 0
        ? testCaseCount
        : null,
    },
    { id: 'test-files', label: 'Test Files', icon: FileText },
    { id: 'reports', label: 'Reports', icon: BarChart3 },
  ];

  return (
    <aside className="w-64 border-r border-[#E0E5F2] dark:border-[#1B1E3A] bg-white dark:bg-[#1B1E3A] flex flex-col justify-between h-screen sticky top-0 z-20 shrink-0 transition-colors duration-200">
      <div className="p-5 flex flex-col gap-6 overflow-y-auto custom-scrollbar">
        {/* Brand Header */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#7357FF] to-[#4318FF] flex items-center justify-center text-white shadow-md shadow-[#4318FF]/25">
              <Code2 className="w-5 h-5 stroke-[2.5]" />
            </div>
            <div>
              <h1 className="font-bold text-[#1B2559] dark:text-white text-base leading-tight tracking-tight">
                UI TestCase Generator
              </h1>
            </div>
          </div>
          <a
            href="/dashboard"
            className="text-xs font-semibold text-[#707EAE] hover:text-[#4318FF] dark:text-[#A3AED0] dark:hover:text-white flex items-center gap-1.5 mt-1 transition-colors"
          >
            &larr; Return to StoryForge AI
          </a>
        </div>

        {/* Navigation Menu */}
        <nav className="flex flex-col gap-1.5 mt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center justify-between gap-3.5 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all duration-150 text-left w-full ${
                  isActive
                    ? 'bg-[#F4F7FE] dark:bg-[#4318FF]/20 text-[#4318FF] dark:text-[#7357FF] font-semibold shadow-xs border-l-4 border-[#4318FF] dark:border-[#7357FF]'
                    : 'text-[#707EAE] dark:text-[#A3AED0] hover:bg-[#F4F7FE] dark:hover:bg-[#11142D]/60 hover:text-[#1B2559] dark:hover:text-white'
                }`}
              >
                <span className="flex items-center gap-3.5">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-[#4318FF] dark:text-[#7357FF] stroke-[2.2]' : 'text-[#A3AED0] dark:text-[#707EAE]'}`} />
                  <span>{item.label}</span>
                </span>

                {/* Dynamic badge for test case count */}
                {item.badge === 'loading' ? (
                  <span className="w-4 h-4 rounded-full border-2 border-[#FF5523] border-t-transparent animate-spin inline-block shrink-0" />
                ) : item.badge ? (
                  <span className="bg-[#FF5523] text-white text-[10px] font-bold px-2 py-0.5 rounded-full min-w-[22px] text-center shrink-0 leading-tight shadow-xs">
                    {item.badge > 999 ? '999+' : item.badge}
                  </span>
                ) : null}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Theme Toggle Footer */}
      <div className="p-4 border-t border-[#E0E5F2] dark:border-[#11142D] bg-[#F4F7FE]/50 dark:bg-[#11142D]/50 flex flex-col gap-3">

        {/* Light / Dark Mode Switcher */}
        <div className="bg-[#E0E5F2]/60 dark:bg-[#11142D] p-1 rounded-xl flex items-center justify-between border border-[#E0E5F2] dark:border-slate-800">
          <button
            onClick={() => setDarkMode(false)}
            className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              !darkMode
                ? 'bg-white dark:bg-slate-700 text-[#FFB800] shadow-xs'
                : 'text-[#A3AED0] hover:text-[#1B2559]'
            }`}
          >
            <Sun className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setDarkMode(true)}
            className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              darkMode
                ? 'bg-[#1B1E3A] text-[#7357FF] shadow-xs'
                : 'text-[#A3AED0] hover:text-[#1B2559]'
            }`}
          >
            <Moon className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </aside>
  );
}
