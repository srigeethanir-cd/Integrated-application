import React from 'react';
import { 
  LayoutGrid, 
  Code2, 
  Terminal, 
  FileCheck2, 
  CheckSquare, 
  Settings as SettingsIcon, 
  Sparkles
} from 'lucide-react';

export default function Sidebar() {
  const activeAccelerator = 'Unit Test Cases';

  const menuItems = [
    { 
      label: 'User Story', 
      icon: LayoutGrid, 
      path: '/dashboard',
    },
    { 
      label: 'UI Code', 
      icon: Code2, 
      path: '/ui-code',
    },
    { 
      label: 'API Code', 
      icon: Terminal, 
      path: '/api-code',
    },
    { 
      label: 'Unit Test Cases', 
      icon: FileCheck2, 
      path: '/unit-test-cases/',
    },
    { 
      label: 'Application Testing', 
      icon: CheckSquare, 
      path: '/application-testing/',
    },
    { 
      label: 'Backend Unit-Testcase Generator', 
      icon: Sparkles, 
      path: '/backend-unit-testcase-generator/',
    },
  ];

  return (
    <aside 
      className="w-[260px] h-screen select-none shrink-0 z-30 flex flex-col justify-between py-6 px-4 relative border-r border-[#2D3748]/50" 
      style={{ backgroundColor: '#1B1B3A' }}
    >
      <div className="space-y-8">
        {/* StoryForge AI Header */}
        <a href="/dashboard" className="flex items-center gap-3 px-2 group">
          <div className="w-8.5 h-8.5 rounded-2xl bg-gradient-to-r from-[#FF602B] to-[#4318FF] flex items-center justify-center shrink-0 shadow-lg shadow-purple-950/60 group-hover:scale-105 transition-transform">
            <Sparkles className="w-4.5 h-4.5 text-white fill-white" />
          </div>
          <span className="text-lg font-extrabold text-white tracking-tight font-sans">
            StoryForge AI
          </span>
        </a>

        {/* Universal Sidebar Menu Items */}
        <nav className="space-y-2">
          {menuItems.map((item) => {
            const isActive = activeAccelerator === item.label;
            const className = `flex items-center justify-between px-4 py-3 rounded-2xl text-xs font-bold transition-all duration-200 group relative ${
              isActive
                ? 'bg-gradient-to-r from-[#FF602B] via-[#7551FF] to-[#4318FF] text-white shadow-lg shadow-indigo-900/40'
                : 'text-[#A0AEC0] hover:text-white hover:bg-white/10'
            }`;

            return (
              <a key={item.label} href={item.path} className={className}>
                <div className="flex items-center gap-3">
                  <item.icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-white' : 'text-[#A0AEC0] group-hover:text-white'}`} />
                  <span>{item.label}</span>
                </div>

                {/* Active Indicator Bar | */}
                {isActive && (
                  <span className="w-1 h-4 bg-white rounded-full shrink-0 shadow-sm" />
                )}
              </a>
            );
          })}
        </nav>
      </div>

      {/* Bottom Settings & User Avatar ('N') */}
      <div className="space-y-4 pt-4 border-t border-white/10">
        <a
          href="/settings"
          className="flex items-center justify-between px-4 py-3 rounded-2xl text-xs font-bold transition-all duration-200 w-full group text-[#A0AEC0] hover:text-white hover:bg-white/10"
        >
          <div className="flex items-center gap-3">
            <SettingsIcon className="w-4 h-4 shrink-0 text-[#A0AEC0] group-hover:text-white" />
            <span>Settings</span>
          </div>
        </a>

        <div className="w-9 h-9 rounded-full bg-[#1A1A2E] border border-gray-700/60 flex items-center justify-center text-white font-extrabold text-xs shadow-md">
          N
        </div>
      </div>
    </aside>
  );
}
