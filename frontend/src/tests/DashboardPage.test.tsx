import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DashboardPage } from '../components/dashboard/DashboardPage';

const evolutionData = {
  fitnessCurves: {
    best: [{ x: 0, y: 0.5 }, { x: 1, y: 0.7 }, { x: 2, y: 0.9 }],
    mean: [{ x: 0, y: 0.3 }, { x: 1, y: 0.5 }, { x: 2, y: 0.6 }],
    std: [{ x: 0, y: 0.1 }, { x: 1, y: 0.08 }, { x: 2, y: 0.05 }],
  },
  currentGeneration: 2,
};

const rlData = {
  metrics: {
    reward: [{ x: 0, y: 10 }, { x: 1, y: 20 }, { x: 2, y: 35 }],
    loss: [{ x: 0, y: 0.5 }, { x: 1, y: 0.3 }, { x: 2, y: 0.1 }],
  },
  currentStep: 1000,
  algorithm: 'PPO',
};

describe('DashboardPage', () => {
  it('renders both tabs', () => {
    render(
      <DashboardPage
        activeTab="evolution"
        onTabChange={vi.fn()}
        evolutionData={evolutionData}
        rlData={null}
      />
    );
    expect(screen.getByText('进化引擎')).toBeInTheDocument();
    expect(screen.getByText('强化学习')).toBeInTheDocument();
  });

  it('shows evolution data on evolution tab', () => {
    render(
      <DashboardPage
        activeTab="evolution"
        onTabChange={vi.fn()}
        evolutionData={evolutionData}
        rlData={null}
      />
    );
    expect(screen.getByText(/当前代数：2/)).toBeInTheDocument();
    expect(screen.getByText('适应度曲线')).toBeInTheDocument();
  });

  it('shows RL data on rl tab', () => {
    render(
      <DashboardPage
        activeTab="rl"
        onTabChange={vi.fn()}
        evolutionData={null}
        rlData={rlData}
      />
    );
    expect(screen.getByText(/步数：1000/)).toBeInTheDocument();
    expect(screen.getByText(/算法：PPO/)).toBeInTheDocument();
  });

  it('calls onTabChange when tab clicked', async () => {
    const onTabChange = vi.fn();
    render(
      <DashboardPage
        activeTab="evolution"
        onTabChange={onTabChange}
        evolutionData={evolutionData}
        rlData={null}
      />
    );
    await userEvent.click(screen.getByText('强化学习'));
    expect(onTabChange).toHaveBeenCalledWith('rl');
  });

  it('shows empty state when no evolution data', () => {
    render(
      <DashboardPage
        activeTab="evolution"
        onTabChange={vi.fn()}
        evolutionData={null}
        rlData={null}
      />
    );
    expect(screen.getByText(/暂无进化数据/)).toBeInTheDocument();
  });

  it('shows empty state when no RL data', () => {
    render(
      <DashboardPage
        activeTab="rl"
        onTabChange={vi.fn()}
        evolutionData={null}
        rlData={null}
      />
    );
    expect(screen.getByText(/暂无训练数据/)).toBeInTheDocument();
  });

  it('renders reward and loss metrics on RL tab', () => {
    render(
      <DashboardPage
        activeTab="rl"
        onTabChange={vi.fn()}
        evolutionData={null}
        rlData={rlData}
      />
    );
    expect(screen.getByText('累计奖励')).toBeInTheDocument();
    expect(screen.getByText('损失函数')).toBeInTheDocument();
  });

  it('shows evolution summary cards', () => {
    render(
      <DashboardPage
        activeTab="evolution"
        onTabChange={vi.fn()}
        evolutionData={evolutionData}
        rlData={null}
      />
    );
    expect(screen.getByText('最优适应度')).toBeInTheDocument();
    expect(screen.getByText('进化代数')).toBeInTheDocument();
    expect(screen.getByText('适应度提升')).toBeInTheDocument();
  });

  it('shows RL comparison chart', () => {
    render(
      <DashboardPage
        activeTab="rl"
        onTabChange={vi.fn()}
        evolutionData={null}
        rlData={rlData}
      />
    );
    expect(screen.getByText(/奖励 vs 损失/)).toBeInTheDocument();
  });
});
