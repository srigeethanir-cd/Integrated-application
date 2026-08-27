'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutGrid, 
  Folder,
  FileText, 
  BookOpen, 
  Layers, 
  Settings as SettingsIcon, 
  Sparkles,
  PanelLeftClose,
  PanelLeftOpen
} from 'lucide-react';
import { usePersonalization, getLogoBorderRadius } from '@/context/PersonalizationContext';

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const { logoUrl, logoShape, sidebarBg, highlightFrom, highlightVia } = usePersonalization();
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
  const isUiCode = pathname.startsWith('/ui-code');
  const isApiCode = pathname.startsWith('/api-code');
  const isUnitTests = pathname.startsWith('/unit-test-cases');
  const isTesting = pathname.startsWith('/application-testing');
  const isBackendGen = pathname.startsWith('/backend-unit-testcase-generator');
  const isSettings = pathname.startsWith('/settings');

  let activeAccelerator = 'User Story';
  if (isUiCode) activeAccelerator = 'UI Code';
  else if (isApiCode) activeAccelerator = 'API Code';
  else if (isUnitTests) activeAccelerator = 'Unit Test Cases';
  else if (isTesting) activeAccelerator = 'Application Testing';
  else if (isBackendGen) activeAccelerator = 'Backend Unit-Testcase Generator';
  else if (isSettings) activeAccelerator = 'Settings';

  const menuItems = [
    { label: 'User Story', icon: LayoutGrid, path: '/dashboard' },
    { label: 'UI Code', icon: Folder, path: '/ui-code' },
    { label: 'API Code', icon: FileText, path: '/api-code' },
    { label: 'Unit Test Cases', icon: BookOpen, path: '/unit-test-cases/' },
    { label: 'Application Testing', icon: Layers, path: '/application-testing/' },
    { label: 'Backend Unit-Testcase Generator', icon: Sparkles, path: '/backend-unit-testcase-generator/' },
  ];

  // Computed gradient for active items
  const activeGradient = `linear-gradient(to right, ${highlightFrom}, ${highlightVia})`;
  const logoRadius = getLogoBorderRadius(logoShape);

  return (
    <aside 
      className={`${collapsed ? 'w-[78px]' : 'w-[260px]'} h-screen select-none shrink-0 z-30 flex flex-col justify-between py-6 px-3 relative border-r border-[#2D3748]/50 transition-all duration-200`} 
      style={{ backgroundColor: sidebarBg }}
    >
      <div className="space-y-7">
        
        {/* StoryForge AI Header with Collapse Toggle */}
        <div className={`flex items-center ${collapsed ? 'justify-center' : 'justify-between'} px-1`}>
          <Link href="/dashboard" className="flex items-center gap-3 group" title="StoryForge AI">
            {logoUrl ? (
              <div 
                className="w-8.5 h-8.5 bg-white/10 p-1 flex items-center justify-center shrink-0 shadow-md group-hover:scale-105 transition-all overflow-hidden"
                style={{ borderRadius: logoRadius }}
              >
                <img src={logoUrl} alt="Logo" className="w-full h-full object-contain" />
              </div>
            ) : (
              <div
                className="w-8.5 h-8.5 flex items-center justify-center shrink-0 shadow-lg group-hover:scale-105 transition-all"
                style={{ background: activeGradient, borderRadius: logoRadius }}
              >
                <Sparkles className="w-4.5 h-4.5 text-white fill-white" />
              </div>
            )}
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
                  <item.icon className={`w-5 h-5 shrink-0 ${isActive ? 'text-white' : 'text-[#8F9BBA] group-hover:text-white'}`} />
                  {!collapsed && <span className="font-semibold text-sm">{item.label}</span>}
                </div>

                {/* Active Indicator Bar | */}
                {isActive && !collapsed && (
                  <span className="w-1.5 h-4 bg-white rounded-full shrink-0 shadow-xs" />
                )}
              </>
            );

            const baseClasses = `flex items-center ${collapsed ? 'justify-center p-3' : 'justify-between px-3.5 py-3'} rounded-xl text-xs transition-all duration-200 group relative`;
            const inactiveClasses = 'text-[#8F9BBA] hover:text-white hover:bg-white/10';

            if (isNginxRoute) {
              return (
                <a
                  key={item.label}
                  href={item.path}
                  className={`${baseClasses} ${isActive ? 'text-white shadow-md' : inactiveClasses}`}
                  style={isActive ? { background: activeGradient } : undefined}
                  title={collapsed ? item.label : undefined}
                >
                  {content}
                </a>
              );
            }

            return (
              <Link
                key={item.label}
                href={item.path}
                className={`${baseClasses} ${isActive ? 'text-white shadow-md' : inactiveClasses}`}
                style={isActive ? { background: activeGradient } : undefined}
                title={collapsed ? item.label : undefined}
              >
                {content}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Bottom Forge Stories Promo & Settings */}
      <div className={`space-y-3 pt-3 border-t border-white/10 flex flex-col ${collapsed ? 'items-center' : ''}`}>
        {!collapsed && (
          <div className="mx-1 p-3.5 rounded-2xl bg-gradient-to-br from-[#2D225A] to-[#1E1B4B] border border-white/10 text-white relative overflow-hidden shadow-md">
            <div className="relative z-10 space-y-1">
              <h4 className="text-xs font-extrabold text-white tracking-tight">Forge Stories</h4>
              <p className="text-[10px] text-[#A0AEC0] leading-tight">Generate AI-powered stories faster</p>
              <Link 
                href="/dashboard"
                className="mt-2 inline-block px-3 py-1 bg-white text-gray-900 font-bold text-[10px] rounded-lg shadow-sm hover:bg-gray-100 transition-colors"
              >
                Try Now
              </Link>
            </div>
            <div className="absolute -right-2 -bottom-2 w-12 h-12 bg-gradient-to-br from-[#7551FF]/40 to-[#FF602B]/30 rounded-xl pointer-events-none" />
          </div>
        )}

        <Link
          href="/settings"
          title={collapsed ? 'Settings' : undefined}
          className={`flex items-center ${collapsed ? 'justify-center p-3' : 'justify-between px-4 py-2.5'} rounded-xl text-xs font-semibold transition-all duration-200 w-full group ${
            activeAccelerator === 'Settings'
              ? 'text-white shadow-md'
              : 'text-[#8F9BBA] hover:text-white hover:bg-white/10'
          }`}
          style={activeAccelerator === 'Settings' ? { background: activeGradient } : undefined}
        >
          <div className={`flex items-center ${collapsed ? 'justify-center' : 'gap-3'}`}>
            <SettingsIcon className="w-5 h-5 shrink-0 text-[#8F9BBA] group-hover:text-white" />
            {!collapsed && <span>Settings</span>}
          </div>
          {activeAccelerator === 'Settings' && !collapsed && (
            <span className="w-1.5 h-4 bg-white rounded-full shrink-0 shadow-xs" />
          )}
        </Link>
      </div>

    </aside>
  );
};
