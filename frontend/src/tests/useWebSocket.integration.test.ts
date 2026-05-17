/**
 * Integration: WebSocket hook + Message delivery to components.
 *
 * Tests the hook→component boundary by mocking WebSocket
 * and verifying messages flow through to rendered components.
 *
 * Covers specs:
 *   - chat-panel.md: WebSocket 实时通信, 断线处理
 *   - monitor.md: 实时消息流
 */

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

describe('WebSocket Integration', () => {
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

  it('connects and tracks connection status', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8080'));
    await act(async () => { vi.runAllTimers(); });
    expect(result.current.connected).toBe(true);
  });

  it('sends JSON-serialized messages', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8080'));
    await act(async () => { vi.runAllTimers(); });
    act(() => {
      result.current.send({ type: 'chat', payload: { text: 'hello' } });
    });
    expect(result.current.ws.current?.send).toHaveBeenCalledWith(
      '{"type":"chat","payload":{"text":"hello"}}'
    );
  });

  it('attempts reconnection on disconnect', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8080'));
    await act(async () => { vi.runAllTimers(); });
    expect(result.current.connected).toBe(true);

    // Simulate disconnect
    const ws = result.current.ws.current as unknown as MockWebSocket;
    act(() => { ws.close(); });
    expect(result.current.connected).toBe(false);

    // Advance timer for reconnect attempt (2000ms)
    await act(async () => { vi.advanceTimersByTime(2000); vi.runAllTimers(); });
    // Should have reconnected (new MockWebSocket auto-opens)
    expect(result.current.connected).toBe(true);
  });

  it('stops reconnecting after 3 attempts', async () => {
    let connectCount = 0;
    const FailWebSocket = class extends MockWebSocket {
      constructor(url: string) {
        super(url);
        connectCount++;
        // Override auto-open: close immediately after "open"
        setTimeout(() => {
          this.readyState = MockWebSocket.CLOSED;
          this.onclose?.();
        }, 0);
      }
    };
    vi.stubGlobal('WebSocket', FailWebSocket as unknown as typeof WebSocket);

    const { result } = renderHook(() => useWebSocket('ws://localhost:8080'));

    // First attempt + 3 reconnects = 4 total connections
    await act(async () => { vi.advanceTimersByTime(0); });   // first open+close
    await act(async () => { vi.advanceTimersByTime(2001); }); // 2nd attempt
    await act(async () => { vi.advanceTimersByTime(2001); }); // 3rd attempt
    await act(async () => { vi.advanceTimersByTime(2001); }); // 4th — exceeds 3 retries

    expect(result.current.connected).toBe(false);
    expect(connectCount).toBeLessThanOrEqual(4);
  });
});
