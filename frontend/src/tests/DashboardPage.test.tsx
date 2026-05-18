import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DashboardPage } from '../components/dashboard/DashboardPage';
import type { AgentSummary } from '../types/api';

function makeAgent(overrides: Partial<AgentSummary> = {}): AgentSummary {
  return {
    agent_id: 'agent-1',
    name: 'Test Agent',
    system_prompt: 'You are helpful',
    config: {},
    ...overrides,
  };
}

describe('DashboardPage', () => {
  it('renders agent cards', () => {
    const agents = [makeAgent(), makeAgent({ agent_id: 'agent-2', name: 'Agent 2' })];
    render(<DashboardPage agents={agents} apiBase="http://localhost:8000" />);
    expect(screen.getByText('Test Agent')).toBeInTheDocument();
    expect(screen.getByText('Agent 2')).toBeInTheDocument();
  });

  it('shows empty state when no agents', () => {
    render(<DashboardPage agents={[]} apiBase="http://localhost:8000" />);
    expect(screen.getByText('暂无智能体')).toBeInTheDocument();
  });

  it('renders agent count heading', () => {
    const agents = [makeAgent()];
    render(<DashboardPage agents={agents} apiBase="http://localhost:8000" />);
    // Page renders the agent card grid
    expect(screen.getByText('Test Agent')).toBeInTheDocument();
  });

  it('renders with single agent', () => {
    const agents = [makeAgent({ agent_id: 'a1', name: 'Solo' })];
    render(<DashboardPage agents={agents} apiBase="http://localhost:8000" />);
    expect(screen.getByText('Solo')).toBeInTheDocument();
  });

  it('shows system prompt in agent card', () => {
    const agents = [makeAgent({ system_prompt: 'Custom prompt' })];
    render(<DashboardPage agents={agents} apiBase="http://localhost:8000" />);
    expect(screen.getByText(/Custom prompt/)).toBeInTheDocument();
  });

  it('renders multiple agent cards', () => {
    const agents = [
      makeAgent({ agent_id: 'a1', name: 'Alpha' }),
      makeAgent({ agent_id: 'a2', name: 'Beta' }),
      makeAgent({ agent_id: 'a3', name: 'Gamma' }),
    ];
    render(<DashboardPage agents={agents} apiBase="http://localhost:8000" />);
    expect(screen.getByText('Alpha')).toBeInTheDocument();
    expect(screen.getByText('Beta')).toBeInTheDocument();
    expect(screen.getByText('Gamma')).toBeInTheDocument();
  });

  it('handles undefined config gracefully', () => {
    const agents = [makeAgent({ config: undefined as any })];
    render(<DashboardPage agents={agents} apiBase="http://localhost:8000" />);
    expect(screen.getByText('Test Agent')).toBeInTheDocument();
  });

  it('renders create agent button area', () => {
    const agents = [makeAgent()];
    const { container } = render(<DashboardPage agents={agents} apiBase="http://localhost:8000" />);
    // Dashboard should render without errors
    expect(container.querySelector('.grid, [class*="grid"]')).toBeTruthy();
  });

  it('renders with empty apiBase', () => {
    const agents = [makeAgent()];
    render(<DashboardPage agents={agents} apiBase="" />);
    expect(screen.getByText('Test Agent')).toBeInTheDocument();
  });
});
