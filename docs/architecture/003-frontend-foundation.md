# ADR-003: Frontend Foundation

## Status

Accepted — Phase 0.3

## Decision

FactoryPilot Web 采用 Ant Design Pro v6 体系作为国内企业级中后台基础，工程运行时使用 Umi Max。

核心依赖：

- React 19
- TypeScript
- Ant Design 6
- ProComponents 3
- Umi Max 4
- TanStack Query
- Zustand
- ECharts（后续 Dashboard / Control Tower）

## Rationale

FactoryPilot 属于数据密集型制造企业内部系统，需要稳定的 Layout、菜单、表格、表单、详情和权限承载能力。Ant Design Pro 比通用海外 SaaS 模板更接近国内 ERP / MES / WMS 的使用习惯，也便于后续借鉴 RuoYi、JeecgBoot 的信息架构和 Arco Design Pro 的 Dashboard 视觉。

## Runtime boundaries

- Web 只通过 HTTP / SSE / WebSocket 与 FastAPI 通信。
- 开发环境 `/api/*` 由 Umi Proxy 转发到 `127.0.0.1:8000`。
- TanStack Query 管理服务端数据状态。
- Zustand 仅保存轻量客户端状态，不替代后端业务状态。
- 当前 Dashboard 使用 Mock KPI；真实业务数据在后续 Phase 接入。

## Ports

- FastAPI: `8000`
- FactoryPilot Web: `8001`
