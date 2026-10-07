# FactoryPilot

FactoryPilot 智造协同决策平台是面向离散制造企业的生产运营与供应链智能决策项目。

当前开发阶段：**Phase 1.1 — Organization / Plant / Department Foundation**。

Phase 0 Engineering Foundation 已完成。Phase 1 正在建立企业身份、组织、权限和审计基础。

## Repository Structure

```text
apps/
  web/
  api/
  simulator/
workers/
packages/
mcp/
infra/
tests/
docs/
```

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

后端容器启动时自动执行 `alembic upgrade head`。

## Phase 1.1 Enterprise APIs

```text
GET/POST   /api/v1/organizations
GET/PATCH  /api/v1/organizations/{organization_id}
GET/POST   /api/v1/plants
GET/PATCH  /api/v1/plants/{plant_id}
GET/POST   /api/v1/departments
GET/PATCH  /api/v1/departments/{department_id}
```

Organization、Plant、Department 均使用 UUID 主键、稳定业务编码、active/inactive 生命周期、UTC 时间戳和 `version` 乐观锁字段。公开 API 不提供物理删除。

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

完成迁移后，Swagger 应出现 `organizations`、`plants`、`departments` 基础 API。

## Architecture Contracts

- [System Architecture Baseline](docs/architecture/007-system-architecture.md)
- [Enterprise Structure Foundation](docs/architecture/008-enterprise-structure-foundation.md)
- [Core Manufacturing Domain ERD](docs/domain/core-domain-erd.md)
- [Domain Event Conventions](docs/domain/domain-events.md)
- [HTTP API Conventions](docs/api/conventions.md)
