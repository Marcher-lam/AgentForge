# Delta Spec: Fitness Framework

> Change: change-20260515-095601 | Domain: fitness | Type: ADDED
> Status: Draft

---

## Feature: Fitness Function Protocol

```gherkin
Feature: 适应度函数接口
  系统 SHALL 提供可扩展的适应度函数框架。

  Scenario: 注册自定义适应度函数
    Given 一个异步适应度函数
    When 注册到引擎
    Then 引擎 SHALL 在每代评估时调用此函数

  Scenario: 适应度函数接收 Individual
    Given 适应度函数签名
    Then 函数 SHALL 接收 Individual 对象
    And Individual SHALL 包含 genome, fitness, metadata 字段

  Scenario: 同步函数自动包装
    Given 一个同步适应度函数（非异步）
    When 注册到引擎
    Then 引擎 SHALL 自动包装为异步执行

  Scenario: batch 评估模式
    Given 适应度函数签名支持 batch
    When 函数接受 list[Individual] 参数
    Then 引擎 SHALL 传入整个种群
    And 函数 SHALL 返回 list[float] 适应度值
    And 引擎 SHALL 优先使用 batch 模式而非逐个评估
```

## Feature: Multi-Objective Fitness

```gherkin
Feature: 多目标加权适应度
  系统 SHALL 支持多目标加权聚合。

  Scenario: 加权适应度计算
    Given 目标函数 A 返回 0.8，权重 0.6
    And 目标函数 B 返回 0.5，权重 0.4
    When 计算加权适应度
    Then 结果 SHALL 为 0.8*0.6 + 0.5*0.4 = 0.68

  Scenario: 权重归一化
    Given 权重 [0.3, 0.5, 0.2]
    When 验证权重
    Then 权重之和 SHALL 为 1.0
    When 权重之和不为 1.0
    Then SHALL 自动归一化
```

## Feature: Constraint Handling

```gherkin
Feature: 约束处理
  系统 SHALL 支持多层约束处理机制。

  Scenario: 边界裁剪
    Given 基因值超出 [lower, upper] 范围
    When 应用边界裁剪
    Then 基因值 SHALL 被裁剪到边界内

  Scenario: 罚函数
    Given 个体违反约束 C1
    When 应用罚函数
    Then 适应度 SHALL 减去罚值 penalty(C1)

  Scenario: 修复算子
    Given 个体不满足约束
    When 应用修复算子
    Then 个体 SHALL 被修复为满足约束的最近合法解
```
