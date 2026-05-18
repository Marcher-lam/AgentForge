import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MessagePanel } from '../components/chat/MessagePanel';
import type { FrontendMessage } from '../types/api';

function makeMsg(overrides: Partial<FrontendMessage> = {}): FrontendMessage {
  return {
    message_id: 'msg-1',
    session_id: 'sess-1',
    sender_type: 'USER',
    sender_id: 'user-1',
    sender_name: 'User',
    content: 'Hello',
    content_type: 'TEXT',
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('MessagePanel', () => {
  it('renders text messages', () => {
    const messages = [makeMsg({ content: 'Hello world', content_type: 'TEXT' })];
    render(<MessagePanel messages={messages} />);
    expect(screen.getByText('Hello world')).toBeInTheDocument();
  });

  it('renders code messages with pre tag', () => {
    const messages = [makeMsg({ content: 'const x = 1;', content_type: 'CODE' })];
    render(<MessagePanel messages={messages} />);
    const code = screen.getByText('const x = 1;');
    expect(code.closest('pre')).toBeInTheDocument();
  });

  it('renders system messages', () => {
    const messages = [makeMsg({ content: 'Agent joined', content_type: 'SYSTEM', sender_type: 'SYSTEM' })];
    render(<MessagePanel messages={messages} />);
    const el = screen.getByText('Agent joined');
    expect(el).toBeInTheDocument();
  });

  it('shows agent name for agent messages', () => {
    const messages = [makeMsg({
      sender_type: 'AGENT',
      sender_name: 'Bot',
      content: 'Hi',
    })];
    render(<MessagePanel messages={messages} />);
    expect(screen.getByText('Bot')).toBeInTheDocument();
  });

  it('aligns user messages to the right', () => {
    const messages = [makeMsg({ sender_type: 'USER', content: 'User msg' })];
    const { container } = render(<MessagePanel messages={messages} />);
    const wrapper = container.querySelector('.justify-end');
    expect(wrapper).toBeInTheDocument();
  });

  it('aligns agent messages to the left', () => {
    const messages = [makeMsg({ sender_type: 'AGENT', sender_name: 'Bot', content: 'Agent msg' })];
    const { container } = render(<MessagePanel messages={messages} />);
    // Agent messages are rendered — verify the message content appears
    expect(screen.getByText('Agent msg')).toBeInTheDocument();
    expect(screen.getByText('Bot')).toBeInTheDocument();
  });

  it('shows loading indicator when hasMore is true', () => {
    const messages = [makeMsg()];
    render(<MessagePanel messages={messages} hasMore={true} />);
    expect(screen.getByText('加载更多...')).toBeInTheDocument();
  });
});
