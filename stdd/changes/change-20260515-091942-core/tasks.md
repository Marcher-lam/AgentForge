# Task Breakdown: Core Skeleton

> Change: change-20260515-091942-core | Priority: P0 | Depends on: none

---

## Task 1: Core Types & Exception Hierarchy
- [x] 定义 AgentState 枚举 + 合法转换表
- [ ] 定义 Message dataclass (frozen, slots) + MessageType 枚举
- [ ] 定义 MessageBus / ToolRegistry / SkillRegistry / MemoryStore Protocol
- [ ] 定义 AgentForgeError 异常层次 (AgentError, BusError, ConfigError)
- [ ] 导出 `agentforge.types.__all__`
- **预估**: 30min | **依赖**: 无

## Task 2: AgentBase ABC + 状态机
- [x] 实现 AgentBase ABC（_on_init/_on_run/_on_stop/_on_destroy 抽象方法）
- [ ] 实现状态机（init/run/stop/destroy + 合法转换校验）
- [ ] 实现 anyio.Lock 并发互斥保护
- [ ] 实现事件回调（on("state_changed", cb) + 事件触发）
- [ ] init 失败不可重试 + destroy 幂等
- [ ] 单元测试：完整生命周期 + 并发互斥 + 非法转换
- **预估**: 45min | **依赖**: Task 1

## Task 3: InProcessMessageBus
- [x] 实现 subscribe(topic, handler) → subscription_id
- [ ] 实现 publish(topic, message) fire-and-forget
- [ ] 实现通配符 (*单层, **递归) topic 匹配
- [ ] 实现 unsubscribe（幂等）
- [ ] 实现 request/response RPC + 超时
- [ ] 实现 handler 有界队列背压 + 投递失败发 message.delivery_failed 事件
- [ ] 实现 Message.to_json()/from_json() 序列化
- [ ] 单元测试：pub/sub + 通配符 + RPC + 背压 + 序列化
- **预估**: 50min | **依赖**: Task 1

## Task 4: WebSocketMessageBus
- [x] 实现 start_server(host, port) WebSocket 服务
- [ ] 实现 connect(url) 客户端连接
- [ ] 实现断线重连（最多 3 次，间隔 2s）+ 服务端持久化订阅恢复
- [ ] 实现心跳（30s ping, 60s pong 超时触发重连）
- [ ] 实现跨进程 pub/sub 消息投递
- [ ] 集成测试：跨进程消息收发 + 重连恢复
- **预估**: 50min | **依赖**: Task 3

## Task 5: 基础设施（日志/配置/优雅关机）
- [x] 实现 structlog 配置（agent_id/topic 上下文）
- [ ] 实现 pyproject.toml [tool.agentforge] + env 配置加载
- [ ] 实现 SIGINT/SIGTERM 优雅关机（先 stop 所有 Agent 再 destroy）
- [ ] 单元测试：配置加载 + 优雅关机
- **预估**: 30min | **依赖**: Task 2

## Task 6: 集成测试 + 覆盖率验证
- [x] Agent 完整生命周期集成测试 (init→run→stop→destroy + 事件序列)
- [ ] 进程内双 Agent pub/sub 集成测试（延迟 < 1ms）
- [ ] WebSocket 跨进程集成测试（延迟 < 50ms）
- [ ] 验证测试覆盖率 ≥ 85%
- **预估**: 30min | **依赖**: Task 4, Task 5
