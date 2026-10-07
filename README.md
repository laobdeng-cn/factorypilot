# FactoryPilot

FactoryPilot 智造协同决策平台是面向离散制造企业的生产运营与供应链智能决策项目。

当前开发阶段：**Phase 0.8 — Architecture Docs + ERD + API/Event Conventions**。

Phase 0 Engineering Foundation 已完成，下一阶段进入 Phase 1 — Identity & Enterprise Foundation。

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

第一次运行：

```powershell
cd <repository-root>
Copy-Item .env.example .env -Force
docker compose up -d --build
```

查看状态：

```powershell
docker compose ps
```

服务地址：

- Frontend: `http://127.0.0.1:8001`
- Backend: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Readiness: `http://127.0.0.1:8000/api/v1/health/ready`
- PostgreSQL host port: `55432`
- Redis host port: `56379`

后端容器会在启动时自动执行 `alembic upgrade head`。前端容器通过 Docker 网络将 `/api/*` 代理到 `backend:8000`。

停止服务：

```powershell
docker compose down
```

删除本项目持久化数据：

```powershell
docker compose down -v
```

## Manual Local Development

仍保留手动开发方式，便于前后端调试。

### Data infrastructure

```powershell
docker compose up -d postgres redis
```

### Backend

```powershell
cd apps\api
Copy-Item .env.example .env -Force
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```powershell
cd <repository-root>
pnpm dev:web
```

## Quality Gates

本地检查：

```powershell
cd apps\api
uv run ruff check .
uv run mypy app
uv run pytest

cd ..\..
pnpm lint:web
pnpm typecheck:web
pnpm test:web
pnpm build:web
docker compose config --quiet
```

GitHub Actions 在 push / pull request 到 `main` 时自动执行 Backend Quality、Frontend Quality 和 Compose Validation。Dependabot 每周检查 npm 与 Python 依赖更新。

## Architecture Contracts

Phase 0.8 已固化以下开发契约：

- [System Architecture Baseline](docs/architecture/007-system-architecture.md)
- [Architecture / ADR Index](docs/architecture/README.md)
- [Core Manufacturing Domain ERD](docs/domain/core-domain-erd.md)
- [Domain Event Conventions](docs/domain/domain-events.md)
- [HTTP API Conventions](docs/api/conventions.md)

核心原则：

- PostgreSQL 是核心事务事实源，Redis 只保存可重建状态。
- 业务状态由所属 bounded context 管理。
- Agent 默认生成建议，不直接绕过业务服务修改核心制造数据。
- 高影响写操作必须具备权限、幂等、审计，并可进入审批。
- 跨领域异步协作遵循领域事件契约，后续核心事务事件采用 Outbox Pattern。

## Phase 0 Exit

Phase 0 Engineering Foundation 已交付：

- Monorepo 工程骨架
- FastAPI Backend Foundation
- Ant Design Pro Frontend Foundation
- FactoryPilot 企业级制造 Dashboard / Navigation
- PostgreSQL 18 + pgvector
- Redis 8
- Alembic baseline
- Docker Compose 一键开发环境
- Backend / Frontend / Compose CI quality gates
- Dependabot dependency monitoring
- 系统架构、领域 ERD、API 与 Event 契约

## Next: Phase 1

Phase 1 — Identity & Enterprise Foundation 将开始真正落地企业基础能力：

- 登录与认证
- Organization / Plant 基础组织模型
- User / Role / Permission
- RBAC + Data Scope
- Audit Log
- 前端登录、用户态与权限菜单
- 首批真实业务表与 Alembic migration

从 Phase 1 开始，新增业务实现应遵循 Phase 0.8 的架构和契约文档；若需要突破既有边界，应先新增 ADR。