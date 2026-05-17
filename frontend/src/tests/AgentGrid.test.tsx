import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AgentGrid } from '../components/grid/AgentGrid';

const agents = [
  {
    agent_id: 'agent-1',
    name: 'Alpha',
    avatar_url: null,
    status: 'ONLINE',
    system_prompt: '你是一个有帮助的AI助手。',
    last_message_preview: 'Hello',
  },
  {
    agent_id: 'agent-2',
    name: 'Beta',
    avatar_url: null,
    status: 'BUSY',
    system_prompt: '你是产品经理。',
    last_message_preview: null,
  },
  {
    agent_id: 'agent-3',
    name: 'Gamma',
    avatar_url: null,
    status: 'OFFLINE',
    system_prompt: '你是设计师。',
    last_message_preview: 'Processing...',
  },
];

describe('AgentGrid', () => {
  it('renders all agent cards', () => {
    render(<AgentGrid agents={agents} apiBase="" />);
    expect(screen.getByText('Alpha')).toBeInTheDocument();
    expect(screen.getByText('Beta')).toBeInTheDocument();
    expect(screen.getByText('Gamma')).toBeInTheDocument();
  });

  it('shows agent count', () => {
    render(<AgentGrid agents={agents} apiBase="" />);
    expect(screen.getByText(/3 个智能体在线/)).toBeInTheDocument();
  });

  it('shows system prompt preview', () => {
    render(<AgentGrid agents={agents} apiBase="" />);
    expect(screen.getAllByText(/你是一个有帮助的AI助手/).length).toBeGreaterThan(0);
  });

  it('shows create button', () => {
    render(<AgentGrid agents={agents} apiBase="" />);
    expect(screen.getByText(/\+ 创建智能体/)).toBeInTheDocument();
  });

  it('shows online status', () => {
    render(<AgentGrid agents={agents} apiBase="" />);
    expect(screen.getByText('在线')).toBeInTheDocument();
  });

  it('clicks agent card without crashing', async () => {
    render(<AgentGrid agents={agents} apiBase="" />);
    const alpha = screen.getByText('Alpha');
    const card = alpha.closest('.cursor-pointer');
    expect(card).toBeTruthy();
    if (card) {
      await userEvent.click(card);
      // Card click triggers fetch (will fail gracefully with empty apiBase)
      // Just verify the grid is still rendered
      expect(screen.getByText('Alpha')).toBeInTheDocument();
    }
  });

  it('shows empty state when no agents', () => {
    render(<AgentGrid agents={[]} apiBase="" />);
    expect(screen.getByText(/暂无智能体/)).toBeInTheDocument();
  });
});
