# FactoryPilot

FactoryPilot 智造协同决策平台是面向离散制造企业的生产运营与供应链智能决策项目。

当前开发阶段：Phase 0.5 — PostgreSQL + Redis + Alembic Data Foundation。

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

## Local Development

### 1. Data infrastructure

```powershell
cd <repository-root>
docker compose up -d postgres redis
docker compose ps
```

### 2. Backend

```powershell
cd apps\api
Copy-Item .env.example .env -Force
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend readiness: `http://127.0.0.1:8000/api/v1/health/ready`

### 3. Frontend

```powershell
cd <repository-root>
pnpm dev:web
```

Frontend: `http://127.0.0.1:8001`

Backend: `http://127.0.0.1:8000`

## Phase 0.5

- PostgreSQL 18 + pgvector local container
- Redis 8 local container
- async SQLAlchemy connection pool
- async Redis client lifecycle
- database and Redis readiness probes
- Alembic infrastructure baseline migration
- local persistent Docker volumes

Manufacturing domain tables remain intentionally deferred until the domain phases.
