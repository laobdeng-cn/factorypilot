# Phase 1.5 — Hierarchical Data Scope

FactoryPilot 的 Phase 1.5 在 RBAC 功能权限之上增加行级数据范围控制。RBAC 回答“用户能否执行某类操作”，Data Scope 回答“该操作可以作用于哪些业务数据”。

## Scope Levels

数据范围按从窄到宽排序：

```text
SELF < DEPARTMENT < PLANT < ORGANIZATION < GLOBAL
```

- `SELF`：用户数据查询只返回本人；
- `DEPARTMENT`：用户与部门数据限制在当前部门；
- `PLANT`：工厂、部门和用户限制在 `primary_plant_id`；
- `ORGANIZATION`：企业资源限制在当前 `organization_id`；
- `GLOBAL`：跨 Organization 全局范围，仅系统管理员默认拥有。

Organization 本身属于租户边界，因此所有非 `GLOBAL` scope 最多只能看到当前 Organization。低层级 scope 在 Plant/Department 端点只暴露与当前身份上下文关联的基础信息。

## Persistent Bindings

Phase 1.5 新增：

```text
role_data_scopes
user_data_scope_overrides
```

每个角色有一个持久化 scope。用户可以有一个显式 override；若 override 存在则优先使用，否则取所有启用角色中最宽的 scope。没有有效角色 scope 时回退到 `SELF`。

内置角色默认值：

```text
system_admin     GLOBAL
factory_manager  PLANT
viewer           ORGANIZATION
```

用户 override 不写入 JWT。和 Role/Permission 一样，每个受保护请求都从数据库重新解析，因此管理员修改 scope 后现有 Access Token 下一次请求即生效。

## Authorization Pipeline

```text
Bearer Token
  -> active auth_session
  -> User
  -> Role / Permission
  -> Effective DataScopeContext
  -> require_permission(...)
  -> query row filter / write target validation
```

`CurrentUser` 包含 `data_scope`，`GET /api/v1/auth/me` 暴露 `data_scope_type` 和 `data_scope_source` 供前端诊断。

## Read Semantics

列表接口在 SQL 查询层追加 scope filter，而不是先读取全部数据后在 Python 过滤：

- Organization：非 GLOBAL 仅当前 Organization；
- Plant：ORGANIZATION 可见本组织全部工厂；更窄 scope 仅当前 primary plant；
- Department：ORGANIZATION 可见本组织；PLANT 仅当前工厂；DEPARTMENT/SELF 仅当前部门；
- User：ORGANIZATION / PLANT / DEPARTMENT 分层过滤；SELF 仅本人。

详情接口对范围外资源返回 `404`，避免通过 ID 探测其他租户或数据域资源。

## Write Semantics

权限检查通过后仍必须满足 Data Scope：

- 创建 Organization 仅 `GLOBAL`；
- 创建 Plant 需要 `GLOBAL`，或当前 Organization 的 `ORGANIZATION` scope；
- 创建 Department 支持 GLOBAL / ORGANIZATION / 当前 PLANT；
- 创建、更新、重置用户密码必须位于调用者有效 scope；
- 更新已有资源时先验证目标资源范围；
- 将用户移动到新的 Plant/Department 时再次验证变更后的归属。

权限存在但数据范围不足时返回：

```json
{
  "error": {
    "code": "auth.data_scope_denied",
    "message": "Target resource is outside current data scope"
  }
}
```

## Scope Management APIs

```text
GET /api/v1/roles/{role_id}/data-scope
PUT /api/v1/roles/{role_id}/data-scope
GET /api/v1/users/{user_id}/data-scope
PUT /api/v1/users/{user_id}/data-scope
```

对应权限：

```text
rbac.data_scope.read
rbac.data_scope.manage
```

系统角色的 scope 不允许通过普通 API 修改。自定义角色可以设置 scope，但管理员不能创建或授予比自身有效 scope 更宽的数据范围。用户 override 同样不能超过操作者自身 scope，从而阻止通过 Data Scope 管理接口横向提权。

## Migration

Alembic revision:

```text
20261008_0006
```

迁移会为既有自定义角色补 `SELF` scope，并为三个内置系统角色写入预定义 scope。
