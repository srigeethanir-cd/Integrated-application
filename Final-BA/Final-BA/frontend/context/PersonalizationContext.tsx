'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';

export interface PersonalizationData {
  logo_url: string | null;
  theme: string;
  updated_at?: string;
  updated_by?: string;
}

interface PersonalizationContextType {
  logoUrl: string | null;
  theme: string;
  isLoading: boolean;
  userRole: string;
  isAdmin: boolean;
  setUserRole: (role: string) => void;
  setTheme: (theme: string) => Promise<boolean>;
  uploadLogo: (file: File) => Promise<string>;
  removeLogo: () => Promise<void>;
  refreshSettings: () => Promise<void>;
}

const DEFAULT_THEME = 'purple-light';

const PersonalizationContext = createContext<PersonalizationContextType>({
  logoUrl: null,
  theme: DEFAULT_THEME,
  isLoading: true,
  userRole: 'administrator',
  isAdmin: true,
  setUserRole: () => {},
  setTheme: async () => false,
  uploadLogo: async () => '',
  removeLogo: async () => {},
  refreshSettings: async () => {},
});

export const usePersonalization = () => useContext(PersonalizationContext);

export const PersonalizationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [logoUrl, setLogoUrl] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('app_custom_logo') || null;
    }
    return null;
  });

  const [theme, setInternalTheme] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('app_active_theme') || DEFAULT_THEME;
    }
    return DEFAULT_THEME;
  });

  const [userRole, setUserRoleState] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('app_user_role') || 'administrator';
    }
    return 'administrator';
  });

  const [isLoading, setIsLoading] = useState<boolean>(true);

  const isAdmin = userRole === 'administrator' || userRole === 'admin';

  const setUserRole = (role: string) => {
    setUserRoleState(role);
    try {
      localStorage.setItem('app_user_role', role);
    } catch {}
  };

  const applyThemeToDom = useCallback((targetTheme: string) => {
    if (typeof document === 'undefined') return;
    const root = document.documentElement;
    root.setAttribute('data-theme', targetTheme);
    if (targetTheme.endsWith('-dark')) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, []);

  const refreshSettings = useCallback(async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      const response = await fetch(`${apiUrl}/api/settings/personalization`, { credentials: 'omit' });
      if (response.ok) {
        const json = await response.json();
        const data: PersonalizationData = json.data || json;
        const fetchedLogo = data.logo_url ?? null;
        const fetchedTheme = data.theme || DEFAULT_THEME;

        setLogoUrl(fetchedLogo);
        setInternalTheme(fetchedTheme);
        applyThemeToDom(fetchedTheme);

        try {
          if (fetchedLogo) localStorage.setItem('app_custom_logo', fetchedLogo);
          else localStorage.removeItem('app_custom_logo');
          localStorage.setItem('app_active_theme', fetchedTheme);
        } catch {}
      }
    } catch (err) {
      console.warn('Could not fetch personalization settings from server:', err);
    } finally {
      setIsLoading(false);
    }
  }, [applyThemeToDom]);

  // Initial load
  useEffect(() => {
    applyThemeToDom(theme);
    refreshSettings();
  }, [applyThemeToDom, refreshSettings, theme]);

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

        socket.onopen = () => {
          // Connection established
        };

        socket.onmessage = (event) => {
          try {
            const parsed = JSON.parse(event.data);
            if (parsed.type === 'PERSONALIZATION_UPDATED' || parsed.type === 'INITIAL_PERSONALIZATION') {
              const data: PersonalizationData = parsed.data;
              const nextLogo = data.logo_url ?? null;
              const nextTheme = data.theme || DEFAULT_THEME;

              setLogoUrl(nextLogo);
              setInternalTheme(nextTheme);
              applyThemeToDom(nextTheme);

              try {
                if (nextLogo) localStorage.setItem('app_custom_logo', nextLogo);
                else localStorage.removeItem('app_custom_logo');
                localStorage.setItem('app_active_theme', nextTheme);
              } catch {}
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
      } catch (err) {
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
  }, [applyThemeToDom]);

  const setTheme = async (newTheme: string): Promise<boolean> => {
    setInternalTheme(newTheme);
    applyThemeToDom(newTheme);
    try {
      localStorage.setItem('app_active_theme', newTheme);
    } catch {}

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      const response = await fetch(`${apiUrl}/api/settings/personalization/theme`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Role': userRole,
        },
        body: JSON.stringify({ theme: newTheme }),
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Failed to save theme to server');
      }
      return true;
    } catch (err) {
      console.error('Failed to update theme on server:', err);
      throw err;
    }
  };

  const uploadLogo = async (file: File): Promise<string> => {
    const formData = new FormData();
    formData.append('file', file);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
    const response = await fetch(`${apiUrl}/api/settings/personalization/logo`, {
      method: 'POST',
      headers: {
        'X-User-Role': userRole,
      },
      body: formData,
    });

    if (!response.ok) {
      const errJson = await response.json().catch(() => ({}));
      throw new Error(errJson.detail || 'Failed to upload logo to Cloudinary');
    }

    const data = await response.json();
    const newLogoUrl = data.logo_url || data.data?.logo_url;

    setLogoUrl(newLogoUrl);
    try {
      if (newLogoUrl) localStorage.setItem('app_custom_logo', newLogoUrl);
    } catch {}

    return newLogoUrl;
  };

  const removeLogo = async (): Promise<void> => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
    const response = await fetch(`${apiUrl}/api/settings/personalization/logo`, {
      method: 'DELETE',
      headers: {
        'X-User-Role': userRole,
      },
    });

    if (!response.ok) {
      const errJson = await response.json().catch(() => ({}));
      throw new Error(errJson.detail || 'Failed to remove logo');
    }

    setLogoUrl(null);
    try {
      localStorage.removeItem('app_custom_logo');
    } catch {}
  };

  return (
    <PersonalizationContext.Provider
      value={{
        logoUrl,
        theme,
        isLoading,
        userRole,
        isAdmin,
        setUserRole,
        setTheme,
        uploadLogo,
        removeLogo,
        refreshSettings,
      }}
    >
      {children}
    </PersonalizationContext.Provider>
  );
};
