'use client';

import React, { useEffect } from 'react';
import { X, Check, Sun, Moon, Laptop } from 'lucide-react';
import { useTheme, THEMES, InterfaceMode } from '../theme/ThemeContext';

export function AppearanceSettingsDrawer() {
  const {
    currentThemeId,
    setTheme,
    interfaceMode,
    setInterfaceMode,
    isSettingsOpen,
    closeSettings,
  } = useTheme();

  // Close on ESC key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isSettingsOpen) {
        closeSettings();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isSettingsOpen, closeSettings]);

  // Prevent background body scrolling when drawer is open
  useEffect(() => {
    if (isSettingsOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isSettingsOpen]);

  return (
    <>
      {/* Dimmed backdrop overlay */}
      <div
        onClick={closeSettings}
        aria-hidden="true"
        className={`fixed inset-0 z-40 bg-black/40 backdrop-blur-[2px] transition-opacity duration-300 ease-out ${
          isSettingsOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
      />

      {/* Slide-in Settings Panel (moves from right to left on open, left to right on close) */}
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Appearance Settings"
        className={`fixed top-0 right-0 z-50 h-full w-full max-w-[450px] bg-white text-[#111827] shadow-2xl flex flex-col border-l border-gray-200 transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] ${
          isSettingsOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100 shrink-0">
          <h2 className="text-xl font-bold text-[#111827] tracking-tight">Appearance Settings</h2>
          <button
            type="button"
            onClick={closeSettings}
            aria-label="Close appearance settings"
            className="p-1.5 rounded-xl text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">
          {/* ── Theme Section ── */}
          <section>
            <div className="flex items-center justify-between mb-3.5">
              <h3 className="text-sm font-bold text-[#1F2937]">Theme</h3>
            </div>

            {/* 2-Column Grid of Theme Cards (matching Image 1 layout) */}
            <div className="grid grid-cols-2 gap-3.5">
              {THEMES.map((theme) => {
                const isSelected = currentThemeId === theme.id;

                return (
                  <div
                    key={theme.id}
                    onClick={() => setTheme(theme.id)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        setTheme(theme.id);
                      }
                    }}
                    className={`group rounded-2xl p-2.5 bg-white transition-all cursor-pointer select-none relative flex flex-col gap-2 ${
                      isSelected
                        ? 'border-2 border-[#EA580C] shadow-sm ring-2 ring-[#EA580C]/10'
                        : 'border border-gray-200 hover:border-gray-300 hover:shadow-xs'
                    }`}
                  >
                    {/* Miniature UI Mockup Frame (Visual preview matching Image 1) */}
                    <div className="w-full h-[76px] rounded-xl overflow-hidden flex border border-[#E2E8F0] bg-[#F8FAFC]">
                      {/* Mini Sidebar */}
                      <div
                        className="w-[36%] h-full p-2 flex flex-col justify-between shrink-0"
                        style={{ backgroundColor: theme.sidebarBg }}
                      >
                        <div className="space-y-1.5">
                          {/* Mini Logo Dot */}
                          <div
                            className="w-1.5 h-1.5 rounded-full"
                            style={{ backgroundColor: theme.previewAccent }}
                          />
                          {/* Mini Nav Skeletons */}
                          <div
                            className="h-1.5 w-full rounded-full"
                            style={{
                              background: `linear-gradient(90deg, ${theme.gradientStart}, ${theme.gradientEnd})`,
                            }}
                          />
                          <div className="h-1.5 w-4/5 rounded-full bg-white/20" />
                          <div className="h-1.5 w-3/4 rounded-full bg-white/20" />
                        </div>
                        <div className="w-1.5 h-1.5 rounded-full bg-white/25" />
                      </div>

                      {/* Mini Content Area */}
                      <div className="flex-1 h-full bg-[#FAFBFC] p-2 flex flex-col justify-between">
                        {/* Header skeleton */}
                        <div className="h-1.5 w-1/2 rounded-full bg-gray-200" />

                        {/* Two central theme gradient bars */}
                        <div className="space-y-1.5 my-auto">
                          <div
                            className="h-2 w-full rounded-md shadow-xs"
                            style={{
                              background: `linear-gradient(90deg, ${theme.gradientStart}, ${theme.gradientEnd})`,
                            }}
                          />
                          <div
                            className="h-2 w-full rounded-md shadow-xs"
                            style={{
                              background: `linear-gradient(90deg, ${theme.gradientStart}, ${theme.gradientEnd})`,
                            }}
                          />
                        </div>

                        {/* Bottom Track Bar with Accent Dots */}
                        <div className="h-1 w-full bg-gray-200/80 rounded-full relative flex items-center justify-between px-0.5">
                          <div
                            className="w-1.5 h-1.5 rounded-full"
                            style={{ backgroundColor: theme.gradientStart }}
                          />
                          <div
                            className="w-2.5 h-1.5 rounded-full"
                            style={{ backgroundColor: theme.gradientEnd }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Card Label & Checkmark */}
                    <div className="flex items-center justify-between px-0.5 pt-0.5 min-h-[22px]">
                      <span
                        className={`text-xs truncate ${
                          isSelected ? 'font-bold text-[#111827]' : 'font-medium text-[#4B5563]'
                        }`}
                      >
                        {theme.name}
                      </span>

                      {isSelected && (
                        <div className="w-4.5 h-4.5 rounded-full bg-[#EA580C] text-white flex items-center justify-center shrink-0 shadow-xs ml-1">
                          <Check className="w-3 h-3 stroke-[3]" />
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          {/* ── Interface Mode Section ── */}
          <section className="pt-4 border-t border-gray-100">
            <h3 className="text-sm font-bold text-[#1F2937] mb-3">Interface Mode</h3>

            <div className="grid grid-cols-3 gap-2.5">
              {(
                [
                  { id: 'light', label: 'Light', icon: Sun },
                  { id: 'dark', label: 'Dark', icon: Moon },
                  { id: 'system', label: 'System', icon: Laptop },
                ] as const
              ).map((mode) => {
                const isActive = interfaceMode === mode.id;

                return (
                  <button
                    key={mode.id}
                    type="button"
                    onClick={() => setInterfaceMode(mode.id as InterfaceMode)}
                    className={`flex flex-col items-center justify-center gap-2 py-3 px-2 rounded-xl border transition-all cursor-pointer ${
                      isActive
                        ? 'border-2 border-[#EA580C] bg-[#FFF8F5] text-[#EA580C] font-bold shadow-xs'
                        : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300 hover:bg-gray-50 font-medium'
                    }`}
                  >
                    <mode.icon className={`w-4.5 h-4.5 ${isActive ? 'text-[#EA580C]' : 'text-gray-500'}`} />
                    <span className="text-xs">{mode.label}</span>
                  </button>
                );
              })}
            </div>
          </section>
        </div>
      </aside>
    </>
  );
}
