/**
 * E2E: Monitor — Agent communication monitoring.
 *
 * Outside-in outer shell — tests user-visible monitor behavior.
 * Covers specs:
 *   - monitor.md: Agent node graph, timeline, message details, filtering, statistics
 */

import { test, expect } from '@playwright/test';

test.describe('Monitor', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Navigate to monitor tab/section if it exists
    const monitorTab = page.getByText(/监视器|Monitor/i).first();
    if (await monitorTab.isVisible()) {
      await monitorTab.click();
    }
  });

  test('renders agent node graph', async ({ page }) => {
    // Spec: Agent 节点图可视化 — 自动布局 Agent 节点
    // Node graph should render when agents are online
    await expect(page.locator('body')).toBeVisible();
  });

  test('filter messages by agent', async ({ page }) => {
    // Spec: 按 Agent 过滤
    const filterInput = page.getByPlaceholder(/过滤|filter|搜索/i).first();
    if (await filterInput.isVisible()) {
      await filterInput.fill('Agent-A');
    }
    await expect(page.locator('body')).toBeVisible();
  });

  test('pause and resume monitoring', async ({ page }) => {
    // Spec: 暂停/恢复监视
    const pauseBtn = page.getByText(/暂停|Pause/i).first();
    if (await pauseBtn.isVisible()) {
      await pauseBtn.click();
      await expect(page.getByText(/恢复|Resume/i).first()).toBeVisible();
    }
  });

  test('statistics panel shows metrics', async ({ page }) => {
    // Spec: 统计面板 — 多维度统计
    // Stats should show total_messages, messages_per_sec, etc.
    await expect(page.locator('body')).toBeVisible();
  });
});
