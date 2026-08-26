'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutGrid, 
  Terminal, 
  FileCheck2, 
  CheckSquare, 
  Settings as SettingsIcon, 
  Sparkles,
  PanelLeftClose,
  PanelLeftOpen
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem('sidebar_collapsed');
      if (saved !== null) setCollapsed(saved === 'true');
    } catch {
      // Ignore localStorage errors
    }
  }, []);

  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem('sidebar_collapsed', String(next));
      } catch {
        // Ignore localStorage errors
      }
      return next;
    });
  };

  // Active accelerator determination
  const isApiCode = pathname.startsWith('/api-code');
  const isUnitTests = pathname.startsWith('/unit-test-cases');
  const isTesting = pathname.startsWith('/application-testing');
  const isBackendGen = pathname.startsWith('/backend-unit-testcase-generator');
  const isSettings = pathname.startsWith('/settings');

  let activeAccelerator = 'User Story';
  if (isApiCode) activeAccelerator = 'API Code';
  else if (isUnitTests) activeAccelerator = 'Unit Test Cases';
  else if (isTesting) activeAccelerator = 'Application Testing';
  else if (isBackendGen) activeAccelerator = 'Backend Unit-Testcase Generator';
  else if (isSettings) activeAccelerator = 'Settings';

  const menuItems = [
    { 
      label: 'User Story', 
      icon: LayoutGrid, 
      path: '/dashboard',
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
      className={`${collapsed ? 'w-[78px]' : 'w-[260px]'} h-screen select-none shrink-0 z-30 flex flex-col justify-between py-6 px-3 relative border-r border-[#2D3748]/50 transition-all duration-200`} 
      style={{ backgroundColor: '#1B1B3A' }}
    >
      <div className="space-y-7">
        
        {/* StoryForge AI Header with Collapse Toggle */}
        <div className={`flex items-center ${collapsed ? 'justify-center' : 'justify-between'} px-1`}>
          <Link href="/dashboard" className="flex items-center gap-3 group" title="StoryForge AI">
            <div className="w-8.5 h-8.5 rounded-2xl bg-gradient-to-r from-[#FF602B] to-[#4318FF] flex items-center justify-center shrink-0 shadow-lg shadow-purple-950/60 group-hover:scale-105 transition-transform">
              <Sparkles className="w-4.5 h-4.5 text-white fill-white" />
            </div>
            {!collapsed && (
              <span className="text-lg font-extrabold text-white tracking-tight font-sans whitespace-nowrap">
                StoryForge AI
              </span>
            )}
          </Link>

          {!collapsed && (
            <button
              onClick={toggleCollapsed}
              title="Collapse sidebar"
              className="p-1.5 rounded-xl text-[#A0AEC0] hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
            >
              <PanelLeftClose className="w-4 h-4" />
            </button>
          )}
        </div>

        {collapsed && (
          <div className="flex justify-center">
            <button
              onClick={toggleCollapsed}
              title="Expand sidebar"
              className="p-1.5 rounded-xl text-[#A0AEC0] hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
            >
              <PanelLeftOpen className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Sidebar Menu Items */}
        <nav className="space-y-2">
          {menuItems.map((item) => {
            const isActive = activeAccelerator === item.label;
            const isNginxRoute = item.path.startsWith('/unit-test-cases') || item.path.startsWith('/application-testing') || item.path.startsWith('/backend-unit-testcase-generator');

            const content = (
              <>
                <div className={`flex items-center ${collapsed ? 'justify-center w-full' : 'gap-3'}`}>
                  <item.icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-white' : 'text-[#A0AEC0] group-hover:text-white'}`} />
                  {!collapsed && <span>{item.label}</span>}
                </div>

                {/* Active Indicator Bar | */}
                {isActive && !collapsed && (
                  <span className="w-1 h-4 bg-white rounded-full shrink-0 shadow-sm" />
                )}
              </>
            );

            const className = `flex items-center ${collapsed ? 'justify-center p-3' : 'justify-between px-4 py-3'} rounded-2xl text-xs font-bold transition-all duration-200 group relative ${
              isActive
                ? 'bg-gradient-to-r from-[#FF602B] via-[#7551FF] to-[#4318FF] text-white shadow-lg shadow-indigo-900/40'
                : 'text-[#A0AEC0] hover:text-white hover:bg-white/10'
            }`;

            if (isNginxRoute) {
              return (
                <a key={item.label} href={item.path} className={className} title={collapsed ? item.label : undefined}>
                  {content}
                </a>
              );
            }

            return (
              <Link key={item.label} href={item.path} className={className} title={collapsed ? item.label : undefined}>
                {content}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Bottom Settings & User Avatar ('N') */}
      <div className={`space-y-4 pt-4 border-t border-white/10 flex flex-col ${collapsed ? 'items-center' : ''}`}>
        <Link
          href="/settings"
          title={collapsed ? 'Settings' : undefined}
          className={`flex items-center ${collapsed ? 'justify-center p-3' : 'justify-between px-4 py-3'} rounded-2xl text-xs font-bold transition-all duration-200 w-full group ${
            activeAccelerator === 'Settings'
              ? 'bg-gradient-to-r from-[#FF602B] to-[#4318FF] text-white shadow-lg shadow-indigo-900/40'
              : 'text-[#A0AEC0] hover:text-white hover:bg-white/10'
          }`}
        >
          <div className={`flex items-center ${collapsed ? 'justify-center' : 'gap-3'}`}>
            <SettingsIcon className="w-4 h-4 shrink-0 text-[#A0AEC0] group-hover:text-white" />
            {!collapsed && <span>Settings</span>}
          </div>
          {activeAccelerator === 'Settings' && !collapsed && (
            <span className="w-1 h-4 bg-white rounded-full shrink-0 shadow-sm" />
          )}
        </Link>

        <div className="w-9 h-9 rounded-full bg-[#1A1A2E] border border-gray-700/60 flex items-center justify-center text-white font-extrabold text-xs shadow-md">
          N
        </div>
      </div>

    </aside>
  );
};
