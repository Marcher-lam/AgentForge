# Design: OAuth2 认证

> Change: change-20260516-oauth2-frontend | Status: Draft

---

## 架构总览

```
┌───────────────────────────────────────────────┐
│  App.tsx (BrowserRouter)                      │
│  ┌──────────────────────────────────────────┐ │
│  │ <Routes>                                 │ │
│  │  <Route path="/login" element={<Login/>}/│ │
│  │  <Route path="/callback" element={<      │ │
│  │    OAuthCallback/>}/>                    │ │
│  │  <Route element={<AuthGuard/>}>          │ │
│  │    <Route path="/" element={<Layout/>}>  │ │
│  │      <Route index element={<Chat/>}/>    │ │
│  │      <Route path="grid" .../>            │ │
│  │      <Route path="monitor" .../>         │ │
│  │      <Route path="dashboard" .../>       │ │
│  │    </Route>                              │ │
│  │  </Route>                                │ │
│  │ </Routes>                                │ │
│  └──────────────────────────────────────────┘ │
└───────────────────────────────────────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Auth Atoms  │  │  Token Mgmt  │  │  API Client  │
│  (Jotai)     │  │  (PKCE+refr) │  │  (intercept) │
└──────────────┘  └──────────────┘  └──────────────┘
```

## 模块设计

### 1. Auth Atoms (`src/auth/atoms.ts`)

```typescript
// 用户信息
const userAtom = atom<User | null>(null)
// Token 对
const tokenAtom = atom<TokenPair | null>(null)
// 认证状态
const isAuthenticatedAtom = atom<boolean>(get => get(tokenAtom) !== null)
// OAuth2 配置
const oauthConfigAtom = atom<OAuthConfig>({
  authorizationEndpoint: '/oauth/authorize',
  tokenEndpoint: '/oauth/token',
  clientId: '',
  redirectUri: '/callback',
  scopes: ['openid', 'profile'],
})
```

### 2. PKCE 工具 (`src/auth/pkce.ts`)

- `generateCodeVerifier()` → 随机字符串 43-128 字符（crypto.getRandomValues）
- `generateCodeChallenge(verifier)` → SHA-256 + Base64URL 编码
- `buildAuthorizationUrl(config, state, challenge)` → 构建授权 URL

### 3. Token 管理 (`src/auth/token.ts`)

- `exchangeCode(code, verifier)` → 用 authorization_code 换 token
- `refreshAccessToken(refreshToken)` → 用 refresh_token 刷新
- Token 过期检查（解码 JWT payload 的 exp 字段）
- 刷新锁（避免并发重复刷新）

### 4. Auth Guard (`src/auth/AuthGuard.tsx`)

- 检查 `isAuthenticatedAtom`
- 未认证 → 重定向到 `/login?redirect=<current_path>`
- 已认证 → 渲染 `<Outlet />`

### 5. API Client (`src/auth/api.ts`)

- `authFetch(url, options)` → 自动注入 Authorization header
- 响应 401 时触发 token 刷新
- 刷新失败重定向到 /login

### 6. Login 页面 (`src/auth/LoginPage.tsx`)

- 显示"使用 GitHub 登录" / "使用 Google 登录"按钮
- 点击后发起 PKCE 流程（生成 verifier → 重定向到 IdP）

### 7. Callback 页面 (`src/auth/OAuthCallback.tsx`)

- 解析 URL 中的 authorization_code 和 state
- 用 code + verifier 换取 token
- 成功后重定向到原始页面或 /

### 8. 路由改造 (`App.tsx`)

- 引入 `BrowserRouter` + `Routes`
- 将 tab-based navigation 改为 route-based
- Login / Callback 为公开路由
- 其他路由嵌套在 AuthGuard 内

## 数据类型

```typescript
interface User {
  id: string
  name: string
  email: string
  avatar?: string
}

interface TokenPair {
  access_token: string
  refresh_token: string
  expires_at: number  // Unix timestamp
  token_type: 'Bearer'
}

interface OAuthConfig {
  authorizationEndpoint: string
  tokenEndpoint: string
  clientId: string
  redirectUri: string
  scopes: string[]
}
```

## 依赖

```
src/auth/
├── atoms.ts           # Jotai auth atoms
├── pkce.ts            # PKCE 工具函数
├── token.ts           # Token 交换/刷新
├── api.ts             # Authenticated fetch wrapper
├── AuthGuard.tsx      # Route guard component
├── LoginPage.tsx      # Login UI
└── OAuthCallback.tsx  # OAuth callback handler
```

**新增依赖**: `react-router-dom` v7

## 关键设计决策

1. **PKCE 而非 implicit flow**：SPA 安全标准，不暴露 token 在 URL fragment
2. **Jotai atoms 而非 Context**：与现有架构一致，atom 可跨组件共享
3. **内存 token 存储**：比 localStorage 更安全，sessionStorage 做页面刷新恢复
4. **react-router-dom**：替代 tab-based navigation，支持 URL 路由和 auth guard
5. **刷新锁**：单例 Promise 避免并发刷新竞争
