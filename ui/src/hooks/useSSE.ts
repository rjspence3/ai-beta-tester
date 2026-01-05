'use client';

import { useEffect, useState, useCallback } from 'react';

export interface SSEEvent {
  type: string;
  timestamp: string;
  [key: string]: unknown;
}

export interface UseSSEOptions {
  onEvent?: (event: SSEEvent) => void;
  onError?: (error: Error) => void;
  onOpen?: () => void;
  onClose?: () => void;
}

export function useSSE(sessionId: string | null, options: UseSSEOptions = {}) {
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  useEffect(() => {
    if (!sessionId) return;

    const eventSource = new EventSource(`/api/sessions/${sessionId}/events`);

    eventSource.onopen = () => {
      setIsConnected(true);
      setError(null);
      options.onOpen?.();
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as SSEEvent;
        setEvents((prev) => [...prev, data]);
        options.onEvent?.(data);
      } catch (e) {
        console.error('Failed to parse SSE event:', e);
      }
    };

    eventSource.onerror = () => {
      const err = new Error('SSE connection error');
      setError(err);
      setIsConnected(false);
      options.onError?.(err);
      eventSource.close();
      options.onClose?.();
    };

    return () => {
      eventSource.close();
      setIsConnected(false);
      options.onClose?.();
    };
  }, [sessionId, options.onEvent, options.onError, options.onOpen, options.onClose]);

  return {
    events,
    isConnected,
    error,
    clearEvents,
  };
}
