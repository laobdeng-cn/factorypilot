# FactoryPilot API

FactoryPilot 主业务 API，基于 FastAPI + Pydantic 2 + SQLAlchemy 2 + Alembic。

## Phase 0.2 范围

- 应用工厂与版本化 API 路由
- Pydantic Settings 配置体系
- 标准化错误响应
- Request ID 与结构化日志
- SQLAlchemy AsyncEngine / AsyncSession
- Alembic 迁移骨架
- Liveness / Readiness 健康检查
- Pytest / Ruff / mypy 基线

## 本地运行（Windows PowerShell）

```powershell
cd apps/api
Copy-Item .env.example .env
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

打开：

- API 文档：http://127.0.0.1:8000/docs
- Liveness：http://127.0.0.1:8000/api/v1/health/live
- Readiness：http://127.0.0.1:8000/api/v1/health/ready

Phase 0.2 默认 `FACTORYPILOT_HEALTHCHECK_DATABASE=false`，因此 PostgreSQL 尚未启动时 API 也可以正常启动。数据库将在 Phase 0.5 接入 Docker Compose 后启用 readiness DB 检查。

## 测试与质量检查

```powershell
uv run pytest
uv run ruff check .
uv run mypy app
```

## Alembic

数据库接入后使用：

```powershell
uv run alembic revision --autogenerate -m "message"
uv run alembic upgrade head
```
