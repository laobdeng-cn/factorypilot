# ADR-002: FastAPI Backend Foundation

Status: Accepted

## Context

FactoryPilot 后端后续需要承载制造领域服务、Agent API、Decision Engine、审批、事件与企业系统集成。Phase 0.2 先建立稳定的应用级基础设施，且在 Phase 0.5 PostgreSQL / Redis Docker 化之前不能强依赖外部服务。

## Decision

- Python 3.13 + FastAPI
- Pydantic Settings 统一读取 `FACTORYPILOT_*` 环境变量
- SQLAlchemy 2 AsyncEngine + asyncpg，连接惰性创建
- Alembic 管理数据库迁移
- 标准错误 envelope：`error.code/message/details/request_id`
- 每个 HTTP 请求生成或透传 `X-Request-ID`
- structlog 作为应用结构化日志基线
- `/api/v1/health/live` 只检查应用存活
- `/api/v1/health/ready` 可配置是否检查数据库
- Phase 0.2 默认关闭数据库 readiness 检查，保证后端可独立启动

## Consequences

后续领域模块只需要接入统一 Settings、DB Session、日志和错误体系，不重复实现横切能力。Phase 0.5 接入 PostgreSQL 后仅需开启数据库 readiness，并开始生成正式 Alembic revision。
