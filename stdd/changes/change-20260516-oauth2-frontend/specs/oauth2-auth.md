# Delta Spec: OAuth2 Authentication

> Change: change-20260516-oauth2-frontend | Domain: auth/oauth2 | Type: ADDED
> Status: Draft

---

## Feature: OAuth2 PKCE 登录流程

```gherkin
Feature: OAuth2 Authorization Code + PKCE
  用户 SHALL 通过 OAuth2 Authorization Code Flow with PKCE 完成认证。

  Scenario: 完整登录流程
    Given 用户未认证
    And 已配置 OAuth2 provider（authorization_endpoint, token_endpoint, client_id）
    When 用户点击"登录"按钮
    Then 系统 SHALL 生成 code_verifier 和 code_challenge（S256）
    And 重定向到 authorization_endpoint（附带 code_challenge）
    When 用户在 IdP 完成授权后被回调（带 authorization_code）
    Then 系统 SHALL 用 authorization_code + code_verifier 换取 token
    And 存储 access_token 和 refresh_token
    And 重定向到主页

  Scenario: PKCE 参数验证
    Given 生成的 code_verifier
    When 计算 code_challenge
    Then code_challenge SHALL 为 code_verifier 的 SHA-256 Base64URL 编码
    And code_verifier 长度 SHALL 在 43-128 字符之间
```

## Feature: 路由守卫

```gherkin
Feature: Auth Guard
  所有受保护路由 SHALL 要求用户已认证。

  Scenario: 未认证访问受保护页面
    Given 用户未认证（无有效 token）
    When 访问 /dashboard
    Then SHALL 重定向到 /login
    And SHALL 保存原始目标 URL 到 redirect_uri 参数

  Scenario: 已认证访问受保护页面
    Given 用户已认证（有效 access_token）
    When 访问 /dashboard
    Then SHALL 正常渲染页面

  Scenario: 登录后回跳原始页面
    Given 用户未认证，访问 /monitor 被重定向到 /login?redirect=/monitor
    When 用户完成 OAuth2 登录
    Then SHALL 重定向到 /monitor（原始目标页面）
```

## Feature: Token 管理

```gherkin
Feature: Token 自动刷新
  系统 SHALL 在 access_token 过期前自动刷新。

  Scenario: Token 过期前自动刷新
    Given access_token 将在 30 秒内过期
    And refresh_token 有效
    When 发起 API 请求
    Then 系统 SHALL 先用 refresh_token 获取新 access_token
    And 再用新 token 发起请求

  Scenario: Refresh token 失败
    Given access_token 已过期
    And refresh_token 刷新失败（如已被撤销）
    When 发起 API 请求
    Then SHALL 清除所有认证状态
    And 重定向到 /login

  Scenario: 并发请求时避免重复刷新
    Given access_token 即将过期
    And 同时有 3 个 API 请求
    Then 系统 SHALL 仅发起一次 refresh 请求
    And 3 个请求 SHALL 都使用刷新后的新 token
```

## Feature: 登出

```gherkin
Feature: 登出清除状态
  用户登出 SHALL 清除所有认证状态。

  Scenario: 登出清除认证
    Given 用户已认证
    When 用户点击"登出"
    Then SHALL 清除 access_token 和 refresh_token
    And 清除 user 信息
    And 重定向到 /login
```

## Feature: API 请求拦截

```gherkin
Feature: API 请求自动附带 Token
  所有 API 请求 SHALL 自动附带 Authorization header。

  Scenario: 请求附带 Bearer token
    Given 用户已认证
    When 发起任何 API 请求
    Then 请求 SHALL 包含 Authorization: Bearer <access_token> header

  Scenario: 未认证时不附带 token
    Given 用户未认证
    When 发起 API 请求
    Then 请求 SHALL NOT 包含 Authorization header
```
