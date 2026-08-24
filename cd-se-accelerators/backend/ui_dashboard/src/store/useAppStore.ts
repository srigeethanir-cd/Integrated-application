import { useState, useEffect } from 'react';

export interface AppStoreState {
  projectId: string;
  selectedStoryId: string | null;
  activeTab: string;
  searchQuery: string;
  isBackendConnected: boolean;
  theme: 'dark' | 'light';
}

export function useAppStore() {
  const [state, setState] = useState<AppStoreState>({
    projectId: 'PROJ-EMP-001',
    selectedStoryId: null,
    activeTab: 'blueprint',
    searchQuery: '',
    isBackendConnected: true,
    theme: 'dark',
  });

  const setProjectId = (projectId: string) => setState((prev) => ({ ...prev, projectId }));
  const setSelectedStoryId = (selectedStoryId: string | null) => setState((prev) => ({ ...prev, selectedStoryId }));
  const setActiveTab = (activeTab: string) => setState((prev) => ({ ...prev, activeTab }));
  const setSearchQuery = (searchQuery: string) => setState((prev) => ({ ...prev, searchQuery }));
  const setIsBackendConnected = (isBackendConnected: boolean) => setState((prev) => ({ ...prev, isBackendConnected }));

  return {
    ...state,
    setProjectId,
    setSelectedStoryId,
    setActiveTab,
    setSearchQuery,
    setIsBackendConnected,
  };
}

export default useAppStore;
