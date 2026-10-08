# Phase 1.4 — Role + Permission + RBAC + API Authorization

## Scope

Phase 1.4 在 Phase 1.3 的可撤销 JWT Session 之上增加功能权限授权层。目标是回答：已认证用户可以执行哪些 API 操作。

数据范围（组织/工厂/部门级 scope）继续留在 Phase 1.5，本阶段只建立功能权限和最基本的组织边界。

## Data Model

```text
User ──< UserRole >── Role ──< RolePermission >── Permission
```

### permissions

权限是稳定的机器可读能力，例如：

```text
enterprise.organization.read
enterprise.organization.manage
enterprise.plant.read
enterprise.plant.manage
enterprise.department.read
enterprise.department.manage
identity.user.read
identity.user.manage
rbac.permission.read
rbac.role.read
rbac.role.manage
rbac.user_role.read
rbac.user_role.manage
```

权限码进入 API 契约后不应随意改名。

### roles

角色聚合一组权限。系统内置角色：

- `system_admin`：全部 Phase 1.4 权限。
- `factory_manager`：工厂/部门基础管理及相关只读能力。
- `viewer`：企业基础信息和用户只读能力。

系统角色为全局模板且不可通过普通 API 修改。自定义角色绑定当前 Organization。

### user_roles

用户可以拥有多个角色。角色变更不要求重新签发 Access Token，因为每个受保护请求都会根据服务端数据库重新加载角色与权限。

这使管理员撤销角色后，现有 JWT 在下一次请求立即失去对应权限。

## Authorization Flow

```text
Bearer Access Token
       │
       ▼
CurrentUser
       │
       ├─ validate JWT
       ├─ validate auth_session
       ├─ validate active user
       └─ load role_codes + permission_codes
                    │
                    ▼
        require_permission("...")
                    │
          ┌─────────┴─────────┐
          │                   │
        allow               403
```

授权失败统一返回：

```json
{
  "error": {
    "code": "auth.permission_denied",
    "message": "Current user does not have the required permission",
    "details": {
      "required_permission": "identity.user.manage"
    }
  }
}
```

## Protected APIs

Phase 1.4 开始保护 Organization、Plant、Department 与 User 管理 API。

读操作使用对应 `.read` 权限，创建、更新和密码重置使用 `.manage` 权限。

`/api/v1/auth/login`、`/auth/refresh` 保持公开；`/auth/me`、`/auth/logout` 只要求有效登录 Session。

## RBAC Management APIs

```text
POST /api/v1/rbac/bootstrap
POST /api/v1/rbac/claim-system-admin
GET  /api/v1/permissions
GET  /api/v1/roles
POST /api/v1/roles
GET  /api/v1/roles/{role_id}
PATCH /api/v1/roles/{role_id}
PUT  /api/v1/roles/{role_id}/permissions
GET  /api/v1/users/{user_id}/roles
PUT  /api/v1/users/{user_id}/roles
```

## Bootstrap Strategy

全新数据库没有 User 时，可调用一次 `/api/v1/rbac/bootstrap` 创建首个 Organization、管理员 User，并授予 `system_admin`。

从 Phase 1.3 升级、数据库已经有 User 但还没有任何 `user_roles` 时，现有用户可先登录，再调用 `/api/v1/rbac/claim-system-admin`。只有在系统中不存在任何用户角色绑定时该接口才可执行。

一旦首次角色绑定完成，Bootstrap 自动关闭并返回 `rbac.bootstrap_closed`。

## Security Properties

- 权限不放进 JWT 作为长期真相，避免权限变更需要等待 Token 过期。
- System Role 权限不可通过普通角色管理 API 修改。
- Refresh Session 撤销与 RBAC 权限是两层独立控制。
- 自定义角色属于 Organization；跨组织数据范围将在 Phase 1.5 进一步收紧。
- 前端菜单隐藏不作为安全边界，后端 API 必须执行 `require_permission()`。

## Phase Boundary

Phase 1.4 不实现：

- Plant / Department 级 Data Scope；
- 行级查询过滤策略；
- Audit Log；
- 前端菜单动态权限。

这些分别进入 Phase 1.5、1.6 和后续前端权限阶段。
