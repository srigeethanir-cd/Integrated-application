'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

export interface ThemeConfig {
  id: string;
  name: string;
  sidebarBg: string;
  gradientStart: string;
  gradientEnd: string;
  accentColor: string;
  previewAccent: string;
}

export const THEMES: ThemeConfig[] = [
  {
    id: 'talvenza',
    name: 'TalvenzA Purple',
    sidebarBg: '#1B1B3A',
    gradientStart: '#FF602B',
    gradientEnd: '#8A2BE2',
    accentColor: '#8A2BE2',
    previewAccent: '#8A2BE2',
  },
  {
    id: 'atlantic',
    name: 'Atlantic',
    sidebarBg: '#0B192C',
    gradientStart: '#003366',
    gradientEnd: '#00D4FF',
    accentColor: '#00D4FF',
    previewAccent: '#00D4FF',
  },
  {
    id: 'evergreen',
    name: 'Evergreen',
    sidebarBg: '#0D2818',
    gradientStart: '#006D77',
    gradientEnd: '#83F2C1',
    accentColor: '#006D77',
    previewAccent: '#006D77',
  },
  {
    id: 'ember',
    name: 'Ember',
    sidebarBg: '#2B1017',
    gradientStart: '#E52D27',
    gradientEnd: '#FF8A00',
    accentColor: '#E52D27',
    previewAccent: '#E52D27',
  },
  {
    id: 'sunrise',
    name: 'Sunrise',
    sidebarBg: '#101935',
    gradientStart: '#F4C430',
    gradientEnd: '#F15F79',
    accentColor: '#F4C430',
    previewAccent: '#F4C430',
  },
  {
    id: 'sunset',
    name: 'Sunset',
    sidebarBg: '#1E162B',
    gradientStart: '#D4145A',
    gradientEnd: '#FBB03B',
    accentColor: '#FF602B',
    previewAccent: '#FF602B',
  },
  {
    id: 'cosmic',
    name: 'Cosmic Dust',
    sidebarBg: '#1E1233',
    gradientStart: '#4A00E0',
    gradientEnd: '#8E2DE2',
    accentColor: '#8E2DE2',
    previewAccent: '#8E2DE2',
  },
  {
    id: 'arctic',
    name: 'Arctic Lights',
    sidebarBg: '#101935',
    gradientStart: '#141E30',
    gradientEnd: '#243B55',
    accentColor: '#3B82F6',
    previewAccent: '#3B82F6',
  },
  {
    id: 'forest',
    name: 'Forest Whisper',
    sidebarBg: '#0B2027',
    gradientStart: '#134E5E',
    gradientEnd: '#71B280',
    accentColor: '#71B280',
    previewAccent: '#71B280',
  },
  {
    id: 'citrus',
    name: 'Citrus Zest',
    sidebarBg: '#2B1410',
    gradientStart: '#E52D27',
    gradientEnd: '#FF8A00',
    accentColor: '#FF8A00',
    previewAccent: '#FF8A00',
  },
  {
    id: 'lagoon',
    name: 'Tropical Lagoon',
    sidebarBg: '#0A2229',
    gradientStart: '#11998E',
    gradientEnd: '#38EF7D',
    accentColor: '#11998E',
    previewAccent: '#38EF7D',
  },
  {
    id: 'orchid',
    name: 'Orchid Mist',
    sidebarBg: '#211129',
    gradientStart: '#8360C3',
    gradientEnd: '#F9A8D4',
    accentColor: '#8360C3',
    previewAccent: '#F9A8D4',
  },
];

export type InterfaceMode = 'light' | 'dark' | 'system';

interface ThemeContextType {
  currentTheme: ThemeConfig;
  currentThemeId: string;
  setTheme: (id: string) => void;
  interfaceMode: InterfaceMode;
  setInterfaceMode: (mode: InterfaceMode) => void;
  isSettingsOpen: boolean;
  openSettings: () => void;
  closeSettings: () => void;
  toggleSettings: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeContextProvider({ children }: { children: React.ReactNode }) {
  const [currentThemeId, setCurrentThemeId] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      try {
        const savedTheme = localStorage.getItem('storyforge_theme_id');
        if (savedTheme && THEMES.some((t) => t.id === savedTheme)) {
          return savedTheme;
        }
      } catch {}
    }
    return 'sunset';
  });

  const [interfaceMode, setInterfaceModeState] = useState<InterfaceMode>(() => {
    if (typeof window !== 'undefined') {
      try {
        const savedMode = localStorage.getItem('storyforge_interface_mode') as InterfaceMode;
        if (savedMode && ['light', 'dark', 'system'].includes(savedMode)) {
          return savedMode;
        }
      } catch {}
    }
    return 'light';
  });

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isMounted, setIsMounted] = useState(false);

  // Initialize from localStorage and handle openSettings query
  useEffect(() => {
    setIsMounted(true);
    try {
      // Listen for openSettings query param e.g. /dashboard?openSettings=true
      if (typeof window !== 'undefined' && window.location.search.includes('openSettings=true')) {
        setIsSettingsOpen(true);
        // Clean URL without refresh
        const url = new URL(window.location.href);
        url.searchParams.delete('openSettings');
        window.history.replaceState(null, '', url.pathname + (url.search ? url.search : ''));
      }
    } catch (e) {
      console.warn('Could not read theme settings from localStorage', e);
    }
  }, []);

  // Listen to cross-tab/cross-window theme updates
  useEffect(() => {
    const handleStorage = (e: StorageEvent) => {
      if (e.key === 'storyforge_theme_id' && e.newValue) {
        if (THEMES.some((t) => t.id === e.newValue)) {
          setCurrentThemeId(e.newValue);
        }
      }
      if (e.key === 'storyforge_interface_mode' && e.newValue) {
        if (['light', 'dark', 'system'].includes(e.newValue)) {
          setInterfaceModeState(e.newValue as InterfaceMode);
        }
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  const currentTheme = THEMES.find((t) => t.id === currentThemeId) || THEMES[5]; // fallback Sunset

  // Apply CSS variables whenever theme changes
  useEffect(() => {
    if (typeof document === 'undefined') return;
    const root = document.documentElement;

    root.style.setProperty('--theme-sidebar-bg', currentTheme.sidebarBg);
    root.style.setProperty('--theme-gradient-start', currentTheme.gradientStart);
    root.style.setProperty('--theme-gradient-end', currentTheme.gradientEnd);
    root.style.setProperty(
      '--theme-gradient',
      `linear-gradient(90deg, ${currentTheme.gradientStart}, ${currentTheme.gradientEnd})`
    );
    root.style.setProperty(
      '--theme-gradient-vertical',
      `linear-gradient(180deg, ${currentTheme.gradientStart}, ${currentTheme.gradientEnd})`
    );
    root.style.setProperty('--theme-accent', currentTheme.accentColor);
    root.style.setProperty('--theme-border-selected', currentTheme.accentColor);

    try {
      localStorage.setItem('storyforge_theme_id', currentTheme.id);
      localStorage.setItem('storyforge_sidebar_bg', currentTheme.sidebarBg);
      localStorage.setItem('storyforge_gradient_start', currentTheme.gradientStart);
      localStorage.setItem('storyforge_gradient_end', currentTheme.gradientEnd);
    } catch (e) {
      console.warn('Could not save theme to localStorage', e);
    }
  }, [currentTheme]);

  // Apply interface mode
  useEffect(() => {
    if (typeof document === 'undefined') return;
    const root = document.documentElement;

    if (interfaceMode === 'dark') {
      root.classList.add('dark');
    } else if (interfaceMode === 'light') {
      root.classList.remove('dark');
    } else {
      // System mode
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      if (prefersDark) {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    }

    try {
      localStorage.setItem('storyforge_interface_mode', interfaceMode);
    } catch (e) {
      console.warn('Could not save mode to localStorage', e);
    }
  }, [interfaceMode]);

  const setTheme = (id: string) => {
    if (THEMES.some((t) => t.id === id)) {
      setCurrentThemeId(id);
    }
  };

  const setInterfaceMode = (mode: InterfaceMode) => {
    setInterfaceModeState(mode);
  };

  const openSettings = () => setIsSettingsOpen(true);
  const closeSettings = () => setIsSettingsOpen(false);
  const toggleSettings = () => setIsSettingsOpen((prev) => !prev);

  return (
    <ThemeContext.Provider
      value={{
        currentTheme,
        currentThemeId,
        setTheme,
        interfaceMode,
        setInterfaceMode,
        isSettingsOpen,
        openSettings,
        closeSettings,
        toggleSettings,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeContextProvider');
  }
  return context;
}
