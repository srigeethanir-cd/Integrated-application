/**
 * Generic async data-fetching hook.
 * Returns { data, loading, error, refetch }.
 */

import { useState, useEffect, useCallback, useRef } from 'react';

export interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useApi<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = [],
  options: { pollingMs?: number; enabled?: boolean } = {},
): UseApiState<T> {
  const { pollingMs, enabled = true } = options;

  const [data, setData]       = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError]     = useState<string | null>(null);
  const mountedRef             = useRef(true);

  const fetchData = useCallback(async () => {
    if (!enabled) return;
    setLoading(true);
    setError(null);
    try {
      const result = await fetcher();
      if (mountedRef.current) setData(result);
    } catch (err: unknown) {
      if (mountedRef.current) {
        const msg =
          err instanceof Error
            ? err.message
            : 'An unexpected error occurred. Please check the API connection.';
        setError(msg);
      }
    } finally {
      if (mountedRef.current) setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, ...deps]);

  useEffect(() => {
    mountedRef.current = true;
    fetchData();
    return () => { mountedRef.current = false; };
  }, [fetchData]);

  // Optional polling
  useEffect(() => {
    if (!pollingMs || !enabled) return;
    const interval = setInterval(fetchData, pollingMs);
    return () => clearInterval(interval);
  }, [fetchData, pollingMs, enabled]);

  return { data, loading, error, refetch: fetchData };
}
