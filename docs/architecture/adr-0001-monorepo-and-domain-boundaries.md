# ADR-0001: Monorepo 与领域边界

- Status: Accepted
- Date: 2026-10-07

## Context

FactoryPilot 同时包含 Web、业务 API、工厂模拟器、Agent Worker、Temporal Worker、MCP Servers、确定性 Decision Engine 和可观测基础设施。若按页面或单一框架组织，后续容易形成强耦合的大型 CRUD 工程。

## Decision

采用 Monorepo，并按运行单元与领域职责划分目录：

- `apps/`: 面向用户或外部系统的应用
- `workers/`: 长任务与 Agent / Workflow worker
- `packages/`: 可复用领域、算法、集成与共享包
- `mcp/`: Agent 可调用的 MCP 服务边界
- `infra/`: 本地与生产基础设施
- `tests/`: 集成、E2E 与 Agent Evaluation
- `docs/`: 架构、API、领域、决策与 Demo 文档

后端业务代码按制造业领域划分，不按前端页面划分。

## Consequences

优点：边界清晰、可独立测试、便于后续拆分服务。代价：需要维护跨包依赖约束和统一开发规范。
