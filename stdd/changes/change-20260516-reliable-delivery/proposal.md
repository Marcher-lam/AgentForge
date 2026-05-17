# Proposal: Agent 通信可靠投递机制

> Change: change-20260516-reliable-delivery | Status: Approved
> Module: `agentforge/bus/`

---

## 问题描述

Agent 通过 InProcessMessageBus 通信时偶发消息丢失，根因：

1. `_deliver()` 使用 `asyncio.ensure_future` 调度 async handler，在 anyio 事件循环下不可靠
2. `QueueFull` 时 `put_nowait` 失败被静默吞掉（line 78-79）
3. handler 异常导致 `_deliver` 循环中断，后续消息全部丢失

## 修复方案

添加可靠投递保障机制：
- **重试投递**：消息投递失败时自动重试（最多 max_retries 次）
- **投递回调通知**：提供 `on_delivery_failed` 回调，让调用方感知丢失
- **异步调度修复**：使用 anyio 兼容的 async 调度替代 `asyncio.ensure_future`
- **异常隔离**：单条消息 handler 异常不影响后续消息投递

## 边界

### IN
- 修复 async handler 调度
- 添加投递重试机制
- 添加投递失败回调
- 异常隔离

### OUT
- 消息持久化（属于长期存储范畴）
- 分布式消息确认（跨进程）
- 消息去重

## 验收标准

- [ ] async handler 在 anyio 下可靠执行
- [ ] QueueFull 时触发重试或失败回调
- [ ] handler 异常不阻断后续消息投递
- [ ] 现有测试全部通过（无回归）
