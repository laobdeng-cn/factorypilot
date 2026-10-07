# FactoryPilot Domain Event Conventions

## Purpose

领域事件用于表达“已经发生的业务事实”，让订单、生产、库存、采购、质量、异常、决策等模块可以解耦协作。

事件不是远程函数调用，也不是把数据库表变化原样广播。事件必须具备明确业务语义。

## Event Naming

统一格式：

```text
factorypilot.<context>.<aggregate>.<event>.v<major>
```

要求：

- 全小写。
- context / aggregate / event 使用 snake_case。
- event 使用过去式或明确完成语义。
- 只有破坏性契约变更才升级 major version。

示例：

```text
factorypilot.order.sales_order.confirmed.v1
factorypilot.production.work_order.released.v1
factorypilot.inventory.material_shortage.detected.v1
factorypilot.procurement.purchase_order.eta_changed.v1
factorypilot.quality.quality_hold.created.v1
factorypilot.exception.exception_case.opened.v1
factorypilot.decision.decision_case.proposed.v1
factorypilot.approval.approval_request.approved.v1
```

## Standard Envelope

```json
{
  "event_id": "uuid",
  "event_type": "factorypilot.order.sales_order.confirmed.v1",
  "event_version": 1,
  "occurred_at": "2026-10-08T03:00:00Z",
  "producer": "factorypilot-api",
  "aggregate_type": "sales_order",
  "aggregate_id": "uuid",
  "aggregate_version": 4,
  "correlation_id": "uuid",
  "causation_id": "uuid-or-null",
  "request_id": "uuid-or-null",
  "tenant_id": "uuid-or-null",
  "plant_id": "uuid-or-null",
  "data": {},
  "metadata": {
    "schema": "factorypilot.order.sales_order.confirmed.v1"
  }
}
```

## Field Rules

### event_id

全局唯一。消费者使用它做去重。

### event_type

稳定事件名。消费者不得依赖 topic 名猜测业务语义。

### occurred_at

事件实际发生时间，UTC ISO 8601。

### aggregate_type / aggregate_id / aggregate_version

标识事件所属聚合。`aggregate_version` 用于检测乱序消费和调试并发问题。

### correlation_id

贯穿一次业务链路。例如：

```text
用户确认销售订单
  → 销售订单确认事件
  → 创建排产任务
  → 物料齐套检查
  → 生成异常/决策建议
```

同一链路应复用同一个 correlation id。

### causation_id

指出当前事件或命令直接由哪个上游事件/命令触发，便于构建因果链。

### request_id

若事件源于 HTTP 请求，保留请求 ID；Worker 自发事件可以为空。

### tenant_id / plant_id

为未来多组织和工厂数据范围预留。消费者不能仅依赖 topic 做数据隔离。

### data

只包含该业务事件的稳定事实，不复制完整数据库行。

## Example Event

```json
{
  "event_id": "c7ff087e-4f2d-4af9-9e04-1bd84743c21d",
  "event_type": "factorypilot.procurement.purchase_order.eta_changed.v1",
  "event_version": 1,
  "occurred_at": "2026-10-08T03:00:00Z",
  "producer": "factorypilot-api",
  "aggregate_type": "purchase_order",
  "aggregate_id": "2ae57e9b-6f38-4e16-9f13-c7b9fc963cbc",
  "aggregate_version": 6,
  "correlation_id": "4507765c-7135-41b6-9877-406483261948",
  "causation_id": null,
  "request_id": "0ea837df-de57-4de7-8d50-af183e45f3d4",
  "tenant_id": null,
  "plant_id": "e8f68baa-5ceb-429b-87f6-7839b292433d",
  "data": {
    "purchase_order_no": "PO202610080021",
    "previous_eta": "2026-10-18",
    "new_eta": "2026-10-25",
    "affected_material_codes": ["MAT-GANIC-001"]
  },
  "metadata": {
    "schema": "factorypilot.procurement.purchase_order.eta_changed.v1"
  }
}
```

## Event vs Command

### Event

表示已经发生：

```text
sales_order.confirmed
quality_hold.created
```

### Command

表示希望系统执行：

```text
confirm_sales_order
release_quality_hold
```

命令可能失败；领域事件一旦发布就是事实。不要把 `confirm_sales_order_requested` 当成订单已确认。

## Delivery Semantics

FactoryPilot 采用 **at-least-once** 思维设计消费者：

- 消费者必须幂等。
- 同一 `event_id` 重复到达不能产生重复副作用。
- 不假设跨聚合全局顺序。
- 同一 aggregate 可以利用 `aggregate_version` 做乱序检测。

## Transactional Outbox Baseline

后续实现领域事件时，核心事务事件应采用 Outbox Pattern：

```text
Business Transaction
  ├─ update aggregate
  └─ insert outbox event
        ↓ same PostgreSQL transaction
Outbox Publisher
        ↓
Event Transport / Worker
```

禁止在数据库事务提交前直接依赖外部消息发送成功，否则会产生“数据库已提交但事件丢失”或反向不一致。

## Consumer Rules

消费者必须：

1. 验证 `event_type` 和 major version。
2. 使用 `event_id` 去重。
3. 记录消费结果或 checkpoint。
4. 对可重试错误和不可重试错误分类。
5. 失败不能静默吞掉。
6. 高影响业务副作用必须再次执行权限/策略/幂等校验。

## Sensitive Data

事件中禁止放：

- 密码、token、API key
- 数据库连接串
- LLM provider secret
- 未脱敏身份证件/个人敏感数据
- 完整 Prompt 中不必要的企业敏感数据

需要详细数据时，消费者通过受控 API 或 Repository 查询。

## Agent-related Events

Agent Runtime 事件与业务事实分开：

```text
factorypilot.agent.run.started.v1
factorypilot.agent.tool_call.completed.v1
factorypilot.agent.run.failed.v1
factorypilot.decision.decision_case.proposed.v1
factorypilot.decision.decision_case.approved.v1
```

`agent.run.completed` 只代表一次 Agent 运行结束，不代表采购、排产或质量业务已经被修改。

## Schema Evolution

兼容变更：

- 新增可选字段。
- 扩充 metadata。

破坏性变更：

- 删除字段。
- 改变字段含义或类型。
- 改变业务语义。

破坏性变更必须发布 `.v2`，并在迁移期允许 v1/v2 消费者并存。

## Phase 0.8 Boundary

本阶段只固化规范，不实现 Event Bus、Outbox 表或消费者。真正实现时必须以本规范为基线，并通过 ADR 记录任何偏离。