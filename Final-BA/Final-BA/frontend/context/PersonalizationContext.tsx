'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';

export type LogoShape = 'square' | 'rounded' | 'circle';

export interface PersonalizationData {
  logo_url: string | null;
  logo_shape: LogoShape;
  sidebar_bg: string;
  highlight_from: string;
  highlight_via: string;
  updated_at?: string;
  updated_by?: string;
}

interface PersonalizationContextType {
  logoUrl: string | null;
  logoShape: LogoShape;
  sidebarBg: string;
  highlightFrom: string;
  highlightVia: string;
  isLoading: boolean;
  userRole: string;
  isAdmin: boolean;
  setUserRole: (role: string) => void;
  savePersonalization: (settings: {
    logoUrl?: string | null;
    logoShape?: LogoShape;
    sidebarBg?: string;
    highlightFrom?: string;
    highlightVia?: string;
  }) => Promise<void>;
  resetPersonalization: () => Promise<void>;
  saveSidebarColors: (bg: string, from: string, via: string) => Promise<void>;
  uploadLogo: (file: File) => Promise<string>;
  removeLogo: () => Promise<void>;
  refreshSettings: () => Promise<void>;
}

const DEFAULTS = {
  logoUrl: null as string | null,
  logoShape: 'rounded' as LogoShape,
  sidebarBg: '#1B1B3A',
  highlightFrom: '#FF5722',
  highlightVia: '#7B3FE4',
};

const PersonalizationContext = createContext<PersonalizationContextType>({
  logoUrl: DEFAULTS.logoUrl,
  logoShape: DEFAULTS.logoShape,
  sidebarBg: DEFAULTS.sidebarBg,
  highlightFrom: DEFAULTS.highlightFrom,
  highlightVia: DEFAULTS.highlightVia,
  isLoading: true,
  userRole: 'administrator',
  isAdmin: true,
  setUserRole: () => {},
  savePersonalization: async () => {},
  resetPersonalization: async () => {},
  saveSidebarColors: async () => {},
  uploadLogo: async () => '',
  removeLogo: async () => {},
  refreshSettings: async () => {},
});

export const usePersonalization = () => useContext(PersonalizationContext);

function readLS(key: string, fallback: string): string {
  if (typeof window === 'undefined') return fallback;
  try { return localStorage.getItem(key) || fallback; } catch { return fallback; }
}
function writeLS(key: string, value: string | null) {
  try { if (value) localStorage.setItem(key, value); else localStorage.removeItem(key); } catch {}
}

export function getLogoBorderRadius(shape: LogoShape): string {
  if (shape === 'square') return '0px';
  if (shape === 'circle') return '50%';
  return '8px';
}

export const PersonalizationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [logoUrl, setLogoUrl] = useState<string | null>(() => readLS('app_custom_logo', '') || null);
  const [logoShape, setLogoShape] = useState<LogoShape>(() => (readLS('app_logo_shape', DEFAULTS.logoShape) as LogoShape) || DEFAULTS.logoShape);
  const [sidebarBg, setSidebarBg] = useState(() => readLS('app_sidebar_bg', DEFAULTS.sidebarBg));
  const [highlightFrom, setHighlightFrom] = useState(() => readLS('app_highlight_from', DEFAULTS.highlightFrom));
  const [highlightVia, setHighlightVia] = useState(() => readLS('app_highlight_via', DEFAULTS.highlightVia));
  const [userRole, setUserRoleState] = useState(() => readLS('app_user_role', 'administrator'));
  const [isLoading, setIsLoading] = useState(true);

  const isAdmin = userRole === 'administrator' || userRole === 'admin';

  const setUserRole = (role: string) => {
    setUserRoleState(role);
    writeLS('app_user_role', role);
  };

  const applyCssVariables = useCallback((bg: string, from: string, via: string, shape: LogoShape) => {
    if (typeof document !== 'undefined' && document.documentElement) {
      document.documentElement.style.setProperty('--sidebar-background', bg);
      document.documentElement.style.setProperty('--sidebar-highlight-from', from);
      document.documentElement.style.setProperty('--sidebar-highlight-via', via);
      document.documentElement.style.setProperty('--logo-border-radius', getLogoBorderRadius(shape));
    }
  }, []);

  const applyState = useCallback((data: PersonalizationData) => {
    const logo = data.logo_url ?? null;
    const shape = (data.logo_shape as LogoShape) || DEFAULTS.logoShape;
    const bg = data.sidebar_bg || DEFAULTS.sidebarBg;
    const from = data.highlight_from || DEFAULTS.highlightFrom;
    const via = data.highlight_via || DEFAULTS.highlightVia;

    setLogoUrl(logo);
    setLogoShape(shape);
    setSidebarBg(bg);
    setHighlightFrom(from);
    setHighlightVia(via);

    applyCssVariables(bg, from, via, shape);

    writeLS('app_custom_logo', logo);
    writeLS('app_logo_shape', shape);
    writeLS('app_sidebar_bg', bg);
    writeLS('app_highlight_from', from);
    writeLS('app_highlight_via', via);
  }, [applyCssVariables]);

  const refreshSettings = useCallback(async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      const response = await fetch(`${apiUrl}/api/settings/personalization`, { credentials: 'omit' });
      if (response.ok) {
        const json = await response.json();
        const data: PersonalizationData = json.data || json;
        applyState(data);
      }
    } catch (err) {
      console.warn('Could not fetch personalization settings from server:', err);
    } finally {
      setIsLoading(false);
    }
  }, [applyState]);

  // Initial load
  useEffect(() => {
    applyCssVariables(sidebarBg, highlightFrom, highlightVia, logoShape);
    refreshSettings();
  }, [applyCssVariables, refreshSettings, sidebarBg, highlightFrom, highlightVia, logoShape]);

  // Real-time WebSocket synchronization
  useEffect(() => {
    if (typeof window === 'undefined') return;

    let socket: WebSocket | null = null;
    let reconnectTimer: NodeJS.Timeout | null = null;
    let isCleanedUp = false;

    const connectWebSocket = () => {
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const wsUrl = `${protocol}//${host}/api/ws/settings`;

        socket = new WebSocket(wsUrl);

        socket.onmessage = (event) => {
          try {
            const parsed = JSON.parse(event.data);
            if (parsed.type === 'PERSONALIZATION_UPDATED' || parsed.type === 'INITIAL_PERSONALIZATION') {
              applyState(parsed.data as PersonalizationData);
            }
          } catch (e) {
            console.error('Error processing personalization WebSocket message:', e);
          }
        };

        socket.onclose = () => {
          if (!isCleanedUp) {
            reconnectTimer = setTimeout(connectWebSocket, 4000);
          }
        };

        socket.onerror = () => {
          socket?.close();
        };
      } catch {
        if (!isCleanedUp) {
          reconnectTimer = setTimeout(connectWebSocket, 4000);
        }
      }
    };

    connectWebSocket();

    return () => {
      isCleanedUp = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (socket) socket.close();
    };
  }, [applyState]);

  const savePersonalization = async (settings: {
    logoUrl?: string | null;
    logoShape?: LogoShape;
    sidebarBg?: string;
    highlightFrom?: string;
    highlightVia?: string;
  }): Promise<void> => {
    const nextLogo = settings.logoUrl !== undefined ? settings.logoUrl : logoUrl;
    const nextShape = settings.logoShape !== undefined ? settings.logoShape : logoShape;
    const nextBg = settings.sidebarBg !== undefined ? settings.sidebarBg : sidebarBg;
    const nextFrom = settings.highlightFrom !== undefined ? settings.highlightFrom : highlightFrom;
    const nextVia = settings.highlightVia !== undefined ? settings.highlightVia : highlightVia;

    // Optimistic UI update
    setLogoUrl(nextLogo);
    setLogoShape(nextShape);
    setSidebarBg(nextBg);
    setHighlightFrom(nextFrom);
    setHighlightVia(nextVia);
    applyCssVariables(nextBg, nextFrom, nextVia, nextShape);

    writeLS('app_custom_logo', nextLogo);
    writeLS('app_logo_shape', nextShape);
    writeLS('app_sidebar_bg', nextBg);
    writeLS('app_highlight_from', nextFrom);
    writeLS('app_highlight_via', nextVia);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
    const response = await fetch(`${apiUrl}/api/settings/personalization`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Role': userRole,
      },
      body: JSON.stringify({
        logo_url: nextLogo,
        logo_shape: nextShape,
        sidebar_bg: nextBg,
        highlight_from: nextFrom,
        highlight_via: nextVia,
      }),
    });

    if (!response.ok) {
      const errJson = await response.json().catch(() => ({}));
      throw new Error(errJson.detail || 'Failed to save personalization settings');
    }
  };

  const resetPersonalization = async (): Promise<void> => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
    const response = await fetch(`${apiUrl}/api/settings/personalization/reset`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Role': userRole,
      },
    });

    if (!response.ok) {
      const errJson = await response.json().catch(() => ({}));
      throw new Error(errJson.detail || 'Failed to reset personalization');
    }

    const json = await response.json();
    const data: PersonalizationData = json.data || json;
    applyState(data);
  };

  const saveSidebarColors = async (bg: string, from: string, via: string): Promise<void> => {
    await savePersonalization({ sidebarBg: bg, highlightFrom: from, highlightVia: via });
  };

  const uploadLogo = async (file: File): Promise<string> => {
    const formData = new FormData();
    formData.append('file', file);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
    const response = await fetch(`${apiUrl}/api/settings/personalization/logo`, {
      method: 'POST',
      headers: { 'X-User-Role': userRole },
      body: formData,
    });

    if (!response.ok) {
      const errJson = await response.json().catch(() => ({}));
      throw new Error(errJson.detail || 'Failed to upload logo');
    }

    const data = await response.json();
    const newLogoUrl = data.logo_url || data.data?.logo_url;

    setLogoUrl(newLogoUrl);
    writeLS('app_custom_logo', newLogoUrl);
    return newLogoUrl;
  };

  const removeLogo = async (): Promise<void> => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
    const response = await fetch(`${apiUrl}/api/settings/personalization/logo`, {
      method: 'DELETE',
      headers: { 'X-User-Role': userRole },
    });

    if (!response.ok) {
      const errJson = await response.json().catch(() => ({}));
      throw new Error(errJson.detail || 'Failed to remove logo');
    }

    setLogoUrl(null);
    writeLS('app_custom_logo', null);
  };

  return (
    <PersonalizationContext.Provider
      value={{
        logoUrl,
        logoShape,
        sidebarBg,
        highlightFrom,
        highlightVia,
        isLoading,
        userRole,
        isAdmin,
        setUserRole,
        savePersonalization,
        resetPersonalization,
        saveSidebarColors,
        uploadLogo,
        removeLogo,
        refreshSettings,
      }}
    >
      {children}
    </PersonalizationContext.Provider>
  );
};
