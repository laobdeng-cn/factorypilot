# ADR-0002 — Contract-first Integration Boundaries

- Status: Accepted
- Date: 2026-10-08

## Context

FactoryPilot 后续将同时存在 Web API、业务模块、Workflow/Agent Worker、Factory Simulator 以及 ERP/MES/WMS/SRM 等外部集成。如果各模块直接共享内部 ORM 结构或自行约定消息格式，后续会出现高耦合、重复副作用、难审计和 Agent 越权写入的问题。

## Decision

FactoryPilot 采用 contract-first 的跨边界协作方式：

1. HTTP 业务接口遵守 `docs/api/conventions.md`。
2. 跨领域异步协作使用 `docs/domain/domain-events.md` 定义的事件 envelope 与命名方式。
3. 核心业务事务事实由所属 bounded context 管理，其他模块不得直接修改其内部表。
4. Agent Runtime 通过应用服务、工具契约或受控命令访问业务能力，不直接以数据库写入代替业务操作。
5. 高影响写操作要求幂等、权限、审计，并可根据策略进入审批。
6. 核心事务事件后续采用 Transactional Outbox，消费者按 at-least-once 语义设计。

## Consequences

### Positive

- API、Worker、Agent 与集成接口边界稳定。
- 降低重复副作用和数据不一致风险。
- 便于回放 Agent 决策与业务因果链。
- 后续从模块化单体拆服务时迁移成本更低。

### Trade-offs

- 需要维护 API/Event schema 与版本。
- 需要额外处理幂等、correlation、outbox 与消费去重。
- 业务开发不能通过跨模块直接写表走捷径。

## Alternatives Rejected

### Shared ORM across all modules

短期开发快，但会把数据库结构变成事实上的公共 API，难以演进。

### Agent direct database writes

缺乏领域校验、权限、审批、幂等和审计边界，不适合制造业高影响操作。

### Best-effort message publish inside business request

无法保证数据库事务与事件发送的一致性，因此后续核心事件采用 Outbox，而不是提交前直接依赖消息发送。