/**
 * WebSocket hook for real-time pipeline updates.
 * Falls back gracefully when the WS endpoint is unavailable.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import type { WsMessage } from '@/services/types';

const WS_BASE = import.meta.env.VITE_WS_BASE_URL ?? 'ws://localhost:8000/ws';

export interface UseWebSocketState {
  lastMessage: WsMessage | null;
  connected: boolean;
  error: string | null;
}

export function useWebSocket(path: string, enabled = true): UseWebSocketState {
  const [lastMessage, setLastMessage] = useState<WsMessage | null>(null);
  const [connected, setConnected]     = useState(false);
  const [error, setError]             = useState<string | null>(null);
  const wsRef                          = useRef<WebSocket | null>(null);
  const reconnectRef                   = useRef<ReturnType<typeof setTimeout>>();

  const connect = useCallback(() => {
    if (!enabled) return;
    try {
      const ws = new WebSocket(`${WS_BASE}${path}`);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        setError(null);
      };

      ws.onmessage = (event: MessageEvent) => {
        try {
          const msg: WsMessage = JSON.parse(event.data as string);
          setLastMessage(msg);
        } catch {
          // ignore malformed frames
        }
      };

      ws.onerror = () => {
        setError('WebSocket connection error — falling back to polling.');
        setConnected(false);
      };

      ws.onclose = () => {
        setConnected(false);
        // Auto-reconnect after 5 s
        reconnectRef.current = setTimeout(connect, 5_000);
      };
    } catch {
      setError('WebSocket not available.');
    }
  }, [path, enabled]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { lastMessage, connected, error };
}
