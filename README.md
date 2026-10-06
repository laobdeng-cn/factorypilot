# FactoryPilot 智造协同决策平台

FactoryPilot 是面向离散制造企业的生产运营与供应链智能决策平台。项目以虚构企业 **华南精密电子有限公司** 为业务背景，通过 ERP / MES / WMS / SRM / QMS 模拟系统、Decision Engine、AI Agent、Human-in-the-loop 与可观测体系，构建从异常感知到业务执行的闭环。

> 当前阶段：Phase 0 — Product & Engineering Foundation

## 核心原则

- 业务系统 + Decision Engine + AI Agent + Human-in-the-loop
- LLM 负责理解、编排、解释与工具调用，不负责 MRP / CTP / APS 等确定性计算
- 高风险写操作必须经过审批并完整审计
- 数据可以虚构，但业务关系必须真实
- 全链路支持 Trace、Evaluation 与可恢复工作流

## 规划技术栈

- Frontend: React / TypeScript / Ant Design Pro / ProComponents / TanStack Query / Zustand / ECharts / AG Grid / React Flow
- Backend: Python 3.13 / FastAPI / Pydantic 2 / SQLAlchemy 2 / Alembic
- Data: PostgreSQL / pgvector / Redis / Redis Streams
- Agent: DeepSeek API / LangGraph / MCP / Structured Output / Tool Calling
- Workflow: Temporal
- Optimization: Google OR-Tools CP-SAT
- Observability: OpenTelemetry / Prometheus / Grafana / Loki
- Testing: Pytest / Vitest / Playwright
- Infrastructure: Docker / Docker Compose / GitHub Actions

## 开发阶段

- Phase 0: Product & Engineering Foundation
- Phase 1: Identity & Enterprise Foundation
- Phase 2: Manufacturing Master Data
- Phase 3: Enterprise Simulator
- Phase 4: Factory Control Tower
- Phase 5: Decision Engine
- Phase 6: Exception Engine
- Phase 7: Agent Runtime
- Phase 8: Manufacturing Agents
- Phase 9: AI Decision & HITL
- Phase 10: Autonomous Workflow
- Phase 11: Evaluation & Governance
- Phase 12: Production Delivery

## Monorepo 目标结构

```text
factorypilot/
├── apps/
│   ├── web/
│   ├── api/
│   └── simulator/
├── workers/
│   ├── agent-worker/
│   └── workflow-worker/
├── packages/
│   ├── domain/
│   ├── decision-engine/
│   ├── agent-runtime/
│   ├── integrations/
│   └── shared/
├── mcp/
├── infra/
├── tests/
├── docs/
└── .github/
```

## License

Development repository for the FactoryPilot project.
