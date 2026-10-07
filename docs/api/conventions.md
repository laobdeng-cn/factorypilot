# FactoryPilot API Conventions

## Scope

本规范适用于 FactoryPilot 业务 API。健康检查等基础设施端点可保持简化响应，但业务端点应遵守本规范。

## Versioning

统一使用 URL 版本：

```text
/api/v1/...
```

破坏性变更必须升级主版本；非破坏性字段新增可以在同一版本演进。

## Resource Naming

- 路径使用复数名词和 kebab-case。
- 资源 ID 放在路径参数中。
- 动作优先建模为状态资源或命令端点，避免任意 RPC 风格。

示例：

```text
GET    /api/v1/sales-orders
GET    /api/v1/sales-orders/{order_id}
POST   /api/v1/sales-orders
PATCH  /api/v1/sales-orders/{order_id}
POST   /api/v1/sales-orders/{order_id}/confirm
```

## Request Metadata

### Request ID

客户端可以传：

```http
X-Request-ID: <uuid-or-trace-id>
```

服务端必须在日志和错误响应中保留该值；未提供时服务端生成。

### Idempotency

对可能重复提交的业务写操作，客户端使用：

```http
Idempotency-Key: <stable-key>
```

适用场景包括：

- 创建采购单/工单等关键业务对象
- 提交审批
- Agent 或 Worker 重试的写操作
- 外部系统 webhook / integration retry

服务端应将同一调用主体、同一路由、同一幂等键视为同一业务命令，并防止重复副作用。

## Success Responses

### Single Resource

直接返回资源对象：

```json
{
  "id": "...",
  "order_no": "SO202610080001",
  "status": "confirmed"
}
```

不额外套 `data` envelope，以减少前后端样板代码。

### Collection Pagination

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 128,
  "total_pages": 7
}
```

查询参数：

```text
?page=1&page_size=20
```

约束：

- `page >= 1`
- 默认 `page_size = 20`
- 推荐最大 `page_size = 100`
- 排序使用 `sort` 和 `order=asc|desc`

高吞吐事件流或时间序列查询后续可以单独采用 cursor pagination，但必须在对应 API 文档中显式声明。

## Filtering

过滤参数使用可读字段名：

```text
GET /api/v1/sales-orders?status=confirmed&customer_id=...&risk_level=high
```

复杂搜索如果超过普通 query 参数表达能力，再引入专用 search endpoint，不在 URL 中传 JSON。

## Error Envelope

所有业务错误统一：

```json
{
  "error": {
    "code": "sales_order.invalid_status_transition",
    "message": "订单当前状态不允许确认",
    "details": {
      "current_status": "completed"
    },
    "request_id": "0ea837df-de57-4de7-8d50-af183e45f3d4"
  }
}
```

字段含义：

- `code`: 稳定机器可读错误码。
- `message`: 面向用户或开发者的安全描述。
- `details`: 可选结构化上下文，不放堆栈或密钥。
- `request_id`: 用于日志关联。

## Error Code Naming

格式：

```text
<context>.<reason>
```

示例：

```text
auth.invalid_credentials
auth.permission_denied
sales_order.not_found
sales_order.invalid_status_transition
inventory.insufficient_available_qty
purchase_order.duplicate_submission
approval.required
system.dependency_unavailable
```

错误码一旦对前端或集成方发布，不应随意改名。

### Authentication Error Codes

Phase 1.3 定义以下稳定错误码：

```text
auth.invalid_credentials
auth.account_locked
auth.account_inactive
auth.missing_token
auth.invalid_token
auth.token_expired
auth.session_not_found
auth.session_revoked
auth.session_expired
auth.refresh_token_reused
auth.user_not_found
```

客户端收到任何 `401` 认证错误时不得自行推测会话仍有效。`auth.refresh_token_reused` 表示服务端已经撤销整个 refresh session，必须重新登录。

## HTTP Status Mapping

| HTTP | 场景 |
| --- | --- |
| 200 | 成功读取或同步更新 |
| 201 | 创建成功 |
| 202 | 已接受异步任务/工作流 |
| 204 | 成功但无响应体 |
| 400 | 请求语义错误 |
| 401 | 未认证、令牌无效、会话失效 |
| 403 | 已认证但无权限或账号停用 |
| 404 | 资源不存在 |
| 409 | 状态冲突、幂等冲突、并发冲突 |
| 422 | 字段验证失败 |
| 423 | 账号临时锁定 |
| 429 | 限流 |
| 500 | 未处理服务端错误 |
| 503 | 数据库、Redis、外部关键依赖不可用 |

## Validation Errors

Pydantic 字段验证错误应转换为 FactoryPilot error envelope，并保留字段级 details。前端不应依赖 FastAPI 默认错误结构作为长期契约。

## Optimistic Concurrency

核心业务聚合预留 `version` 字段。修改关键资源时可使用：

```http
If-Match: "<version>"
```

或请求体中的明确 version。版本不一致返回 `409 Conflict`，避免后写覆盖先写。

## Dates and Time

- API 时间使用 ISO 8601。
- 持久化统一 UTC。
- 业务日期（如承诺交期）如果只有日期语义，使用 `YYYY-MM-DD`，不要伪造时区时间。
- 工厂本地展示由前端或服务层根据 plant timezone 转换。

## Enum Values

枚举值使用稳定英文小写 snake_case，例如：

```text
confirmed
in_production
on_hold
high
critical
```

中文只用于 UI 文案，不进入数据库状态值和跨系统契约。

## Authentication and Authorization

Phase 1.3 起统一使用 Bearer access token + server-side refresh session：

```http
Authorization: Bearer <access_token>
```

约定：

- access token 默认 15 分钟；
- refresh token 默认 7 天并在每次 refresh 时轮换；
- 原始 refresh token 不落库，只保存 SHA-256 digest；
- access token 必须关联一个仍有效、未撤销的 `auth_sessions` 记录；
- logout、密码修改、账号停用、refresh token 重放检测均可立即撤销 session；
- 路由层解析 Current User Context；
- Phase 1.4 起由 Application/Domain 层继续验证 RBAC 与数据范围；
- 不仅依赖前端菜单隐藏；
- 高影响写操作同时检查 RBAC、数据范围和审批策略。

## Audit Requirements

以下操作必须形成审计记录：

- 权限/角色变更
- 订单关键状态变化
- 排产确认
- 采购确认与优先级变更
- Quality Hold 创建/释放
- 审批结果
- Agent 发起或执行的业务动作

审计信息至少包含 actor、action、resource、before/after 摘要、request_id、timestamp、source。

## OpenAPI

FastAPI OpenAPI 是开发期可执行契约，但不是唯一文档。新增业务 API 时应：

- 明确 request/response schema
- 填写 summary / description
- 声明可能的错误码
- 避免返回未类型化 `dict[str, Any]`
- 保持 schema 名称稳定

## API Review Checklist

新增端点前检查：

1. 是否属于正确 bounded context？
2. 是否复用了已有资源而不是创建重复概念？
3. 是否定义了权限与数据范围？
4. 写操作是否需要幂等？
5. 是否需要乐观锁？
6. 是否会产生领域事件？
7. 是否需要审计？
8. 错误码是否稳定且可定位？
9. 是否会泄露内部堆栈、连接串或模型密钥？
