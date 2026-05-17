import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '../hooks/useWebSocket';

class MockWebSocket {
  static OPEN = 1;
  static CLOSED = 3;
  readyState = MockWebSocket.OPEN;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((e: Event) => void) | null = null;
  onmessage: ((e: MessageEvent) => void) | null = null;
  send = vi.fn();
  close = vi.fn(() => {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.();
  });

  url: string;
  constructor(url: string) {
    this.url = url;
    setTimeout(() => this.onopen?.(), 0);
  }
}

describe('useWebSocket', () => {
  let originalWebSocket: typeof WebSocket;

  beforeEach(() => {
    originalWebSocket = globalThis.WebSocket;
    vi.stubGlobal('WebSocket', MockWebSocket as unknown as typeof WebSocket);
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
    globalThis.WebSocket = originalWebSocket;
  });

  it('does not connect when url is null', () => {
    const { result } = renderHook(() => useWebSocket(null));
    expect(result.current.connected).toBe(false);
  });

  it('connects when url is provided', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8080'));
    await act(async () => { vi.runAllTimers(); });
    expect(result.current.connected).toBe(true);
  });

  it('sends data via websocket', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8080'));
    await act(async () => { vi.runAllTimers(); });
    act(() => { result.current.send({ type: 'test' }); });
    expect(result.current.ws.current?.send).toHaveBeenCalledWith('{"type":"test"}');
  });
});
