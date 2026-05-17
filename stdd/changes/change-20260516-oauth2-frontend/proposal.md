# Proposal: OAuth2 认证支持

> Change: change-20260516-oauth2-frontend | Status: Approved
> Module: `frontend/src/auth/`

---

## 需求概述

为 frontend-ui 添加 OAuth2 认证，使用 Authorization Code Flow with PKCE（SPA 标准方案），保护所有页面路由和 API 调用。

## 当前状态

- 前端无路由库（tab-based navigation via useState）
- 无认证代码
- 状态管理使用 Jotai
- API 调用通过 useWebSocket hook（无 auth header）

## 边界

### IN（包含）
- 添加 react-router-dom 路由系统
- OAuth2 Authorization Code + PKCE 登录流程
- Login 页面组件
- Auth Guard（路由守卫）
- Token 管理（access_token / refresh_token / 自动刷新）
- Jotai auth atoms（user, token, isAuthenticated）
- API 请求拦截器（自动附带 Authorization header）

### OUT（不包含）
- 后端 OAuth2 Provider 实现（假设已有 Identity Provider）
- 用户注册/管理界面
- 多租户/角色权限（RBAC）
- SSO / SAML / LDAP 集成
- MFA / 2FA

## 隐含约束

1. 使用 Authorization Code Flow with PKCE（SPA 标准，不暴露 client_secret）
2. Token 存储在内存中（Jotai atom），refresh_token 可存 httpOnly cookie（后端负责）
3. 支持 GitHub / Google 等主流 IdP
4. Token 过期前 30 秒自动刷新
5. 未认证用户重定向到 /login

## 技术选型

| 组件 | 技术 | 理由 |
|------|------|------|
| 路由 | react-router-dom v7 | React 标准路由，支持 loader/guard |
| 状态 | Jotai atoms | 与现有架构一致 |
| HTTP | fetch + interceptor | 轻量，无需 axios |
| PKCE | 原生 crypto API | 浏览器原生支持，零依赖 |
| Token 存储 | 内存 (atom) + sessionStorage | 安全性 + 持久化平衡 |

## 验收标准

- [ ] 未认证用户访问任何页面被重定向到 /login
- [ ] OAuth2 PKCE 流程正常完成
- [ ] Token 过期后自动刷新
- [ ] 刷新失败重定向到 /login
- [ ] API 请求自动附带 Bearer token
- [ ] 登出清除所有认证状态
