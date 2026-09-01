'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutGrid, 
  BookOpen, 
  Layers, 
  Settings as SettingsIcon, 
  Sparkles,
  FileText,
  Code2,
  PanelLeftClose,
  PanelLeftOpen
} from 'lucide-react';
import { useTheme } from '@/components/theme/ThemeContext';
import { useLanguage } from '@/components/i18n/LanguageContext';

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const { openSettings } = useTheme();
  const { t } = useLanguage();

  const [isEmbedded, setIsEmbedded] = useState(false);
  useEffect(() => {
    if (typeof window !== 'undefined' && (window.self !== window.top || window.location.search.includes('embedded=true'))) {
      setIsEmbedded(true);
    }
  }, []);

  if (isEmbedded) return null;
  const [collapsed, setCollapsed] = useState<boolean>(() => {
    try {
      const saved = localStorage.getItem('sidebar_collapsed');
      if (saved !== null) {
        return saved === 'true';
      }
    } catch {
      // Ignore localStorage errors
    }
    return false;
  });

  const [customLogo, setCustomLogo] = useState<string | null>(null);

  useEffect(() => {
    const loadLogo = () => {
      try {
        const saved = localStorage.getItem('app_logo_url');
        setCustomLogo(saved);
      } catch {
        // Ignore localStorage errors
      }
    };
    loadLogo();
    window.addEventListener('app_logo_updated', loadLogo);
    return () => window.removeEventListener('app_logo_updated', loadLogo);
  }, []);

  useEffect(() => {
    try {
      const saved = localStorage.getItem('sidebar_collapsed');
      if (saved !== null) {
        setCollapsed(saved === 'true');
      }
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
  const isUnitTests = pathname.startsWith('/unit-test-cases') || pathname.startsWith('/unit-tests');
  const isTesting = pathname.startsWith('/application-testing') || pathname.startsWith('/testing');
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
    { 
      label: t('userStory'), 
      key: 'User Story',
      icon: LayoutGrid, 
      path: '/dashboard',
    },
    { 
      label: t('apiCode'), 
      key: 'API Code',
      icon: FileText, 
      path: '/api-code',
    },
    { 
      label: t('unitTestCases'), 
      key: 'Unit Test Cases',
      icon: BookOpen, 
      path: '/unit-test-cases',
    },
    { 
      label: t('appTesting'), 
      key: 'Application Testing',
      icon: Layers, 
      path: '/application-testing',
    },
    { 
      label: t('backendGenerator'), 
      key: 'Backend Unit-Testcase Generator',
      icon: Sparkles, 
      path: '/backend-unit-testcase-generator',
    },
  ];

  return (
    <aside 
      className={`${collapsed ? 'w-[78px]' : 'w-[260px]'} h-screen select-none shrink-0 z-30 flex flex-col justify-between py-6 px-3 relative border-r border-[#2D3748]/50 transition-all duration-200`} 
      style={{ backgroundColor: 'var(--theme-sidebar-bg, #1B1B3A)' }}
    >
      <div className="space-y-7">
        
        {/* StoryForge AI Header with Collapse Toggle */}
        <div className={`flex items-center ${collapsed ? 'justify-center' : 'justify-between'} px-1`}>
          <Link href="/dashboard" className="flex items-center gap-3 group" title="StoryForge AI">
            {customLogo ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={customLogo}
                alt="StoryForge Logo"
                className="w-8.5 h-8.5 rounded-2xl object-cover shrink-0 shadow-lg shadow-purple-950/40 group-hover:scale-105 transition-transform"
              />
            ) : (
              <div className="w-8.5 h-8.5 rounded-2xl bg-gradient-to-r from-[#FF602B] to-[#4318FF] flex items-center justify-center shrink-0 shadow-lg shadow-purple-950/60 group-hover:scale-105 transition-transform">
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
            const isActive = activeAccelerator === item.key;

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

            const className = `flex items-center ${collapsed ? 'justify-center p-3' : 'justify-between px-3.5 py-3'} rounded-xl text-xs transition-all duration-200 group relative ${
              isActive
                ? 'text-white shadow-md'
                : 'text-[#8F9BBA] hover:text-white hover:bg-white/10'
            }`;

            const activeStyle = isActive ? { background: 'var(--theme-gradient)' } : undefined;

            return (
              <Link
                key={item.key}
                href={item.path}
                className={className}
                style={activeStyle}
                title={collapsed ? item.label : undefined}
                onClick={(e) => {
                  if (isActive) {
                    e.preventDefault();
                  }
                }}
              >
                {content}
              </Link>
            );
          })}
        </nav>

        {/* UI Code — Disabled / Coming Soon */}
        <div className="pt-3 mt-2 border-t border-white/10">
          <button
            type="button"
            disabled
            title={collapsed ? `${t('uiCode')} — Coming Soon` : 'Coming Soon'}
            className={`flex items-center ${collapsed ? 'justify-center p-3' : 'justify-between px-3.5 py-3'} rounded-xl text-xs w-full cursor-not-allowed opacity-50 text-[#636e82]`}
          >
            <div className={`flex items-center ${collapsed ? 'justify-center' : 'gap-3'}`}>
              <Code2 className="w-5 h-5 shrink-0 text-[#636e82]" />
              {!collapsed && <span className="font-semibold text-sm text-[#636e82]">{t('uiCode')}</span>}
            </div>
            {!collapsed && (
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#636e82] bg-white/5 border border-white/10 px-2 py-0.5 rounded-md">
                Soon
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Bottom Settings Button (Slides in Appearance Settings drawer) */}
      <div className={`space-y-3 pt-3 border-t border-white/10 flex flex-col ${collapsed ? 'items-center' : ''}`}>
        <button
          type="button"
          onClick={openSettings}
          title={collapsed ? t('settings') : undefined}
          className={`flex items-center ${collapsed ? 'justify-center p-3' : 'justify-between px-4 py-2.5'} rounded-xl text-xs font-semibold transition-all duration-200 w-full group cursor-pointer text-[#8F9BBA] hover:text-white hover:bg-white/10`}
        >
          <div className={`flex items-center ${collapsed ? 'justify-center' : 'gap-3'}`}>
            <SettingsIcon className="w-5 h-5 shrink-0 text-[#8F9BBA] group-hover:text-white" />
            {!collapsed && <span>{t('settings')}</span>}
          </div>
        </button>
      </div>

    </aside>
  );
};
