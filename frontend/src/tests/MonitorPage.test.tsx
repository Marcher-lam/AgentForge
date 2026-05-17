import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MonitorPage } from '../components/monitor/MonitorPage';
import type { MonitorMessage } from '../types/api';

const messages: MonitorMessage[] = [
  {
    message_id: 'm-1',
    sender_id: 'sender-abc-123',
    receiver_id: 'receiver-def-456',
    topic: 'task.execute',
    message_type: 'request',
    payload: { action: 'run' },
    timestamp: '2026-01-01T10:00:00Z',
  },
  {
    message_id: 'm-2',
    sender_id: 'sender-ghi-789',
    receiver_id: null,
    topic: 'broadcast.status',
    message_type: 'notification',
    payload: { status: 'done' },
    timestamp: '2026-01-01T10:01:00Z',
  },
];

describe('MonitorPage', () => {
  it('renders message list with topics', () => {
    render(
      <MonitorPage
        messages={messages}
        nodes={[]}
        edges={[]}
        isPaused={false}
        onTogglePause={vi.fn()}
      />
    );
    expect(screen.getByText('task.execute')).toBeInTheDocument();
    expect(screen.getByText('broadcast.status')).toBeInTheDocument();
  });

  it('shows pause/resume button', () => {
    render(
      <MonitorPage
        messages={messages}
        nodes={[]}
        edges={[]}
        isPaused={false}
        onTogglePause={vi.fn()}
      />
    );
    expect(screen.getByText('Pause')).toBeInTheDocument();
  });

  it('shows Resume when paused', () => {
    render(
      <MonitorPage
        messages={messages}
        nodes={[]}
        edges={[]}
        isPaused={true}
        onTogglePause={vi.fn()}
      />
    );
    expect(screen.getByText('Resume')).toBeInTheDocument();
  });

  it('toggles pause on button click', async () => {
    const onToggle = vi.fn();
    render(
      <MonitorPage
        messages={messages}
        nodes={[]}
        edges={[]}
        isPaused={false}
        onTogglePause={onToggle}
      />
    );
    await userEvent.click(screen.getByText('Pause'));
    expect(onToggle).toHaveBeenCalledOnce();
  });

  it('filters messages by keyword', async () => {
    render(
      <MonitorPage
        messages={messages}
        nodes={[]}
        edges={[]}
        isPaused={false}
        onTogglePause={vi.fn()}
      />
    );
    const input = screen.getByPlaceholderText(/按关键词/);
    await userEvent.type(input, 'task');
    expect(screen.getByText('task.execute')).toBeInTheDocument();
    expect(screen.queryByText('broadcast.status')).not.toBeInTheDocument();
  });

  it('shows message detail on click', async () => {
    render(
      <MonitorPage
        messages={messages}
        nodes={[]}
        edges={[]}
        isPaused={false}
        onTogglePause={vi.fn()}
      />
    );
    await userEvent.click(screen.getByText('task.execute'));
    expect(screen.getByText('消息详情')).toBeInTheDocument();
    expect(screen.getByText(/sender-abc-123/)).toBeInTheDocument();
  });
});
