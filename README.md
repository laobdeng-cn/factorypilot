# FactoryPilot

FactoryPilot 智造协同决策平台是面向离散制造企业的生产运营与供应链智能决策项目。

当前开发阶段：**Phase 1.5 — Organization / Plant / Department / Self Data Scope**。

Phase 0 Engineering Foundation 已完成。Phase 1 正在建立企业身份、组织、权限、数据范围和审计基础。

## One-command Development Stack

```powershell
cd <repository-root>
Copy-Item .env.example .env -Force
docker compose up -d --build
```

服务地址：

- Frontend: `http://127.0.0.1:8001`
- Backend: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Readiness: `http://127.0.0.1:8000/api/v1/health/ready`
- PostgreSQL host port: `55432`
- Redis host port: `56379`

## Enterprise APIs

Organization、Plant、Department API 同时执行 RBAC 功能权限与 Data Scope 行级过滤。

```text
GET/POST   /api/v1/organizations
GET/PATCH  /api/v1/organizations/{organization_id}
GET/POST   /api/v1/plants
GET/PATCH  /api/v1/plants/{plant_id}
GET/POST   /api/v1/departments
GET/PATCH  /api/v1/departments/{department_id}
```

列表查询在 SQL 层按有效 scope 限制数据；详情读取对越界资源返回 `404`；写操作在权限校验后继续验证目标资源是否位于可管理范围。

## Identity APIs

```text
GET/POST   /api/v1/users
GET/PATCH  /api/v1/users/{user_id}
POST       /api/v1/users/{user_id}/password
POST       /api/v1/auth/login
POST       /api/v1/auth/refresh
GET        /api/v1/auth/me
POST       /api/v1/auth/logout
```

`/api/v1/auth/me` 返回 `role_codes`、`permission_codes`、`data_scope_type` 与 `data_scope_source`。Role、Permission 和 Data Scope 都在每个受保护请求中从服务端数据库重新解析，管理员调整后不需要等待 JWT 过期。

## RBAC + Data Scope APIs

```text
POST       /api/v1/rbac/bootstrap
POST       /api/v1/rbac/claim-system-admin
GET        /api/v1/permissions
GET/POST   /api/v1/roles
GET/PATCH  /api/v1/roles/{role_id}
PUT        /api/v1/roles/{role_id}/permissions
GET/PUT    /api/v1/roles/{role_id}/data-scope
GET/PUT    /api/v1/users/{user_id}/roles
GET/PUT    /api/v1/users/{user_id}/data-scope
```

数据范围从窄到宽：

```text
SELF < DEPARTMENT < PLANT < ORGANIZATION < GLOBAL
```

内置角色：

- `system_admin`：`GLOBAL`，全部当前管理权限；
- `factory_manager`：`PLANT`，工厂/部门管理与相关只读能力；
- `viewer`：`ORGANIZATION`，企业基础信息与用户只读能力。

用户可配置显式 Data Scope override；存在 override 时优先于角色 scope。管理员不能给角色或用户授予比自身有效 scope 更宽的范围。

全新数据库可通过 `/api/v1/rbac/bootstrap` 一次性创建首个 Organization 和系统管理员。若从旧阶段升级且已经存在用户但尚未分配任何角色，先登录后调用 `/api/v1/rbac/claim-system-admin`。首次角色绑定完成后 Bootstrap 自动关闭。

Passwords are stored only as Argon2id hashes. Five consecutive failed attempts temporarily lock the account for 15 minutes.

Phase 1.3 提供 15 分钟 JWT Access Token 和 7 天轮换 Refresh Token，并使用服务端 `auth_sessions` 实现即时撤销。Phase 1.4 增加 RBAC 功能权限，Phase 1.5 在其上增加行级 Data Scope。

For any non-development deployment, replace the documented development JWT secret with a high-entropy deployment secret.

## Manual Backend Verification

```powershell
cd apps\api
uv sync
uv run alembic upgrade head
uv run alembic current
uv run ruff check .
uv run mypy app
uv run pytest
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

完成迁移后，`alembic current` 应为 `20261008_0006 (head)`。Swagger 应出现 `enterprise`、`identity` 和 `rbac` 分组。

## Architecture Contracts

- [System Architecture Baseline](docs/architecture/007-system-architecture.md)
- [Enterprise Structure Foundation](docs/architecture/008-enterprise-structure-foundation.md)
- [User + Password Authentication](docs/architecture/009-user-password-authentication.md)
- [JWT Session Authentication](docs/architecture/010-jwt-session-authentication.md)
- [RBAC + API Authorization](docs/architecture/011-rbac-api-authorization.md)
- [Hierarchical Data Scope](docs/architecture/012-data-scope.md)
- [Core Manufacturing Domain ERD](docs/domain/core-domain-erd.md)
- [Domain Event Conventions](docs/domain/domain-events.md)
- [HTTP API Conventions](docs/api/conventions.md)
