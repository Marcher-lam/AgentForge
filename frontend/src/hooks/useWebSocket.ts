import { useCallback, useEffect, useRef, useState } from 'react';
import { useSetAtom } from 'jotai';
import { connectionStatusAtom } from '../atoms';

export function useWebSocket(url: string | null) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const setConnStatus = useSetAtom(connectionStatusAtom);
  const reconnectRef = useRef(0);

  const connect = useCallback(() => {
    if (!url) return;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      setConnStatus('connected');
      reconnectRef.current = 0;
    };

    ws.onclose = () => {
      setConnected(false);
      setConnStatus('disconnected');
      if (reconnectRef.current < 3) {
        reconnectRef.current++;
        setTimeout(connect, 2000);
        setConnStatus('reconnecting');
      }
    };

    ws.onerror = () => ws.close();
  }, [url, setConnStatus]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  return { connected, send, ws: wsRef };
}
