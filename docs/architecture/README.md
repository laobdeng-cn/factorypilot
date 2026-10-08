# Architecture

FactoryPilot 架构文档与 ADR 索引。

## Phase Documents

- [002 Backend Foundation](./002-backend-foundation.md)
- [003 Frontend Foundation](./003-frontend-foundation.md)
- [003 Frontend UI Baseline](./003-frontend-ui-baseline.md)
- [004 Data Infrastructure](./004-data-infrastructure.md)
- [005 Docker Compose Development Environment](./005-compose-development-environment.md)
- [006 CI and Code Quality](./006-ci-and-code-quality.md)
- [007 System Architecture Baseline](./007-system-architecture.md)
- [008 Enterprise Structure Foundation](./008-enterprise-structure-foundation.md)
- [009 User + Password Authentication](./009-user-password-authentication.md)
- [010 JWT Session Authentication](./010-jwt-session-authentication.md)
- [011 RBAC + API Authorization](./011-rbac-api-authorization.md)

## Architecture Decision Records

- [ADR-0001 Monorepo 与领域边界](./adr-0001-monorepo-and-domain-boundaries.md)
- [ADR-0002 Contract-first Integration Boundaries](./adr-0002-contract-first-integration.md)

## Related Contracts

- [Core Domain ERD](../domain/core-domain-erd.md)
- [Domain Event Conventions](../domain/domain-events.md)
- [API Conventions](../api/conventions.md)

新的架构边界、跨领域依赖、持久化策略或 Agent 高影响写入策略发生实质变化时，应新增 ADR，而不是只在实现代码中隐式改变。
