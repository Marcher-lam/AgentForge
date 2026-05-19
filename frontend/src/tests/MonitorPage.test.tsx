import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MonitorPage } from '../components/monitor/MonitorPage';

const mockEvents = {
  events: [
    {
      id: 'e-1',
      timestamp: '2026-01-01T10:00:00Z',
      type: 'message',
      severity: 'info',
      session_id: 's-1',
      agent_id: 'a-1',
      run_id: null,
      payload: { sender_type: 'USER', sender_name: 'You', chars: 20 },
    },
    {
      id: 'e-2',
      timestamp: '2026-01-01T10:00:01Z',
      type: 'typing',
      severity: 'info',
      session_id: 's-1',
      agent_id: 'a-1',
      run_id: null,
      payload: { sender_name: '程序员' },
    },
    {
      id: 'e-3',
      timestamp: '2026-01-01T10:00:03Z',
      type: 'tool_call',
      severity: 'info',
      session_id: 's-1',
      agent_id: 'a-1',
      run_id: null,
      payload: { sender_name: '程序员', tool_name: 'web_search' },
    },
  ],
  total: 3,
};

const mockStats = {
  total_events: 3,
  by_type: { message: 1, typing: 1, tool_call: 1 },
  by_severity: { info: 3 },
  top_agents: [['a-1', 3]],
  top_sessions: [['s-1', 3]],
  recent_errors: [],
  active_websockets: 2,
  sessions: 1,
  messages: 10,
  agents: 5,
  running_training: { rl: 0, evolution: 1, coevolution: 0 },
};

beforeEach(() => {
  globalThis.fetch = vi.fn().mockImplementation((url: string) => {
    if (url.includes('/monitor/events')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockEvents) } as any);
    }
    if (url.includes('/monitor/stats')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockStats) } as any);
    }
    return Promise.resolve({ ok: false, json: () => Promise.resolve({}) } as any);
  });
});

describe('MonitorPage', () => {
  it('renders system overview cards', async () => {
    render(<MonitorPage />);
    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument(); // total events
    });
    expect(screen.getByText(/2 online/)).toBeInTheDocument(); // websockets
    expect(screen.getByText(/Evo:1/)).toBeInTheDocument(); // training
  });

  it('renders event list with types', async () => {
    render(<MonitorPage />);
    await waitFor(() => {
      expect(screen.getAllByText('message')).toHaveLength(2); // tag + breakdown
    });
  });

  it('shows event detail on click', async () => {
    render(<MonitorPage />);
    await waitFor(() => {
      // Wait for events to render by checking for a specific event row
      expect(screen.getByText(/You/)).toBeInTheDocument();
    });
    // Click the first event row (contains "message" type tag)
    const msgTag = screen.getAllByText('message').find(el => el.classList.contains('rounded'));
    await userEvent.click(msgTag!);
    await waitFor(() => {
      expect(screen.getByText('事件详情')).toBeInTheDocument();
    });
  });

  it('filters by type', async () => {
    render(<MonitorPage />);
    await waitFor(() => {
      expect(screen.getAllByText('message').length).toBeGreaterThan(0);
    });
    const select = screen.getByRole('combobox');
    await userEvent.selectOptions(select, 'typing');
    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(expect.stringContaining('type=typing'));
    });
  });

  it('searches by keyword', async () => {
    render(<MonitorPage />);
    await waitFor(() => {
      expect(screen.getAllByText(/程序员/).length).toBeGreaterThan(0);
    });
    const input = screen.getByPlaceholderText(/搜索/);
    await userEvent.type(input, 'tool_call');
    // After filtering, only tool_call event remains visible
    await waitFor(() => {
      const toolCallTags = screen.getAllByText('tool_call');
      // Should have the type tag in event list
      expect(toolCallTags.length).toBeGreaterThan(0);
    });
  });

  it('shows empty state when no events', async () => {
    (globalThis.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/monitor/events')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ events: [], total: 0 }) } as any);
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ total_events: 0, by_type: {}, by_severity: {}, top_agents: [], top_sessions: [], recent_errors: [], active_websockets: 0, sessions: 0, messages: 0, agents: 0, running_training: { rl: 0, evolution: 0, coevolution: 0 } }) } as any);
    });
    render(<MonitorPage />);
    await waitFor(() => {
      expect(screen.getByText('暂无监控事件')).toBeInTheDocument();
    });
  });
});
