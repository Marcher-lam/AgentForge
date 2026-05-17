# Tasks: OAuth2 认证

> Change: change-20260516-oauth2-frontend | Status: Ready

---

## Phase 1: 基础设施

- [ ] T1.1: 安装 react-router-dom 依赖
- [ ] T1.2: 定义 TypeScript 类型（User, TokenPair, OAuthConfig）
- [ ] T1.3: 单元测试 — 类型验证和序列化

**验收**: react-router-dom 安装成功，类型定义完整

## Phase 2: Auth Atoms

- [ ] T2.1: 实现 auth atoms（userAtom, tokenAtom, isAuthenticatedAtom, oauthConfigAtom）
- [ ] T2.2: 单元测试 — 初始状态、状态更新、派生 atom

**验收**: spec 中的认证状态管理可验证

## Phase 3: PKCE 工具

- [ ] T3.1: 实现 generateCodeVerifier（crypto.getRandomValues）
- [ ] T3.2: 实现 generateCodeChallenge（SHA-256 + Base64URL）
- [ ] T3.3: 实现 buildAuthorizationUrl
- [ ] T3.4: 单元测试 — verifier 长度、challenge 编码正确性、URL 构建
- [ ] T3.5: 单元测试 — PKCE 完整流程（verifier → challenge → URL → 验证）

**验收**: spec PKCE 参数验证场景通过

## Phase 4: Token 管理

- [ ] T4.1: 实现 exchangeCode（authorization_code → token）
- [ ] T4.2: 实现 refreshAccessToken（refresh_token → new access_token）
- [ ] T4.3: 实现刷新锁（避免并发重复刷新）
- [ ] T4.4: 实现 token 过期检查（JWT exp 解码）
- [ ] T4.5: 单元测试 — code 换 token（mock fetch）
- [ ] T4.6: 单元测试 — token 刷新成功
- [ ] T4.7: 单元测试 — token 刷新失败清除状态
- [ ] T4.8: 单元测试 — 并发刷新锁（仅一次 refresh 请求）

**验收**: spec Token 管理全部场景通过

## Phase 5: Auth Guard

- [ ] T5.1: 实现 AuthGuard 组件（检查 isAuthenticated → redirect/login）
- [ ] T5.2: 实现 redirect_uri 参数保存
- [ ] T5.3: 单元测试 — 未认证重定向到 /login
- [ ] T5.4: 单元测试 — 已认证正常渲染
- [ ] T5.5: 单元测试 — 登录后回跳原始页面

**验收**: spec 路由守卫全部场景通过

## Phase 6: Login & Callback 页面

- [ ] T6.1: 实现 LoginPage（"使用 GitHub 登录"按钮 + PKCE 发起）
- [ ] T6.2: 实现 OAuthCallback（解析 code + state → 换 token → 重定向）
- [ ] T6.3: 单元测试 — Login 按钮点击触发重定向
- [ ] T6.4: 单元测试 — Callback 解析 code 并换取 token
- [ ] T6.5: 单元测试 — Callback 错误处理（code 缺失、state 不匹配）

**验收**: spec OAuth2 PKCE 登录流程通过

## Phase 7: API 拦截器

- [ ] T7.1: 实现 authFetch（自动注入 Authorization header）
- [ ] T7.2: 实现 401 响应自动刷新逻辑
- [ ] T7.3: 单元测试 — 请求附带 Bearer token
- [ ] T7.4: 单元测试 — 401 触发刷新后重试
- [ ] T7.5: 单元测试 — 未认证时不附带 token

**验收**: spec API 请求拦截全部场景通过

## Phase 8: 路由改造

- [ ] T8.1: App.tsx 引入 BrowserRouter + Routes
- [ ] T8.2: Tab navigation → Route-based navigation
- [ ] T8.3: 添加 /login, /callback 公开路由
- [ ] T8.4: 其他路由嵌套在 AuthGuard 内
- [ ] T8.5: 集成测试 — 完整路由导航 + 认证流程
- [ ] T8.6: 集成测试 — 登出清除状态

**验收**: spec 登出场景通过，全流程端到端可验证

## Phase 9: 登出

- [ ] T9.1: 实现登出逻辑（清除 tokens + user + 重定向）
- [ ] T9.2: 添加登出按钮到 UI
- [ ] T9.3: 单元测试 — 登出清除所有状态

**验收**: spec 登出场景通过

---

## 依赖关系

```
T1 → T2, T3, T4（基础设施先就绪）
T2 → T5（AuthGuard 依赖 auth atoms）
T3 → T6（Login/Callback 依赖 PKCE）
T4 → T7（API 拦截依赖 token 管理）
T5, T6, T7 → T8（路由改造需要所有 auth 模块）
T8 → T9（登出需要路由改造完成）
```

## 预估工时

| Phase | 预估 |
|-------|------|
| Phase 1 | 0.5h |
| Phase 2 | 0.5h |
| Phase 3 | 1h |
| Phase 4 | 1.5h |
| Phase 5 | 1h |
| Phase 6 | 1h |
| Phase 7 | 1h |
| Phase 8 | 1.5h |
| Phase 9 | 0.5h |
| **合计** | **8.5h** |
