# FactoryPilot

FactoryPilot 智造协同决策平台是面向离散制造企业的生产运营与供应链智能决策项目。

当前开发阶段：Phase 0.7 — CI + Code Quality。

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

## Phase 0.7

- GitHub Actions backend quality gate
- GitHub Actions frontend quality gate
- Docker Compose configuration validation
- Ruff + mypy + pytest
- Biome + TypeScript + Vitest + production build
- CI concurrency cancellation
- weekly Dependabot dependency monitoring
- CI architecture documentation
