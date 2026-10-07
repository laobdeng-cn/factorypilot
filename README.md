# FactoryPilot

FactoryPilot 智造协同决策平台是面向离散制造企业的生产运营与供应链智能决策项目。

当前开发阶段：**Phase 1.3 — JWT Access / Refresh Token + Session Revocation**。

Phase 0 Engineering Foundation 已完成。Phase 1 正在建立企业身份、组织、权限和审计基础。

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

```text
GET/POST   /api/v1/organizations
GET/PATCH  /api/v1/organizations/{organization_id}
GET/POST   /api/v1/plants
GET/PATCH  /api/v1/plants/{plant_id}
GET/POST   /api/v1/departments
GET/PATCH  /api/v1/departments/{department_id}
```

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

Passwords are stored only as Argon2id hashes. Five consecutive failed attempts temporarily lock the account for 15 minutes.

Phase 1.3 adds 15-minute JWT access tokens and seven-day rotating refresh tokens backed by server-side `auth_sessions`. Raw refresh tokens are not persisted. Logout, password changes, account deactivation, and refresh-token reuse revoke the relevant session immediately.

`/api/v1/auth/me` and `/api/v1/auth/logout` require `Authorization: Bearer <access_token>`. User-management permission enforcement is intentionally reserved for Phase 1.4 RBAC.

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

完成迁移后，`alembic current` 应为 `20261008_0004 (head)`，Swagger 的 `identity` 分组应出现 login、refresh、me 与 logout。

## Architecture Contracts

- [System Architecture Baseline](docs/architecture/007-system-architecture.md)
- [Enterprise Structure Foundation](docs/architecture/008-enterprise-structure-foundation.md)
- [User + Password Authentication](docs/architecture/009-user-password-authentication.md)
- [JWT Session Authentication](docs/architecture/010-jwt-session-authentication.md)
- [Core Manufacturing Domain ERD](docs/domain/core-domain-erd.md)
- [Domain Event Conventions](docs/domain/domain-events.md)
- [HTTP API Conventions](docs/api/conventions.md)
