# FactoryPilot

FactoryPilot 智造协同决策平台是面向离散制造企业的生产运营与供应链智能决策项目。

当前开发阶段：Phase 0.4 — FactoryPilot UI / Navigation / Dashboard。

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

### Backend

```powershell
cd apps\api
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```powershell
cd <repository-root>
pnpm dev:web
```

Frontend: `http://127.0.0.1:8001`

Backend: `http://127.0.0.1:8000`

## Phase 0.4

- Ant Design Pro / Ant Design enterprise UI baseline
- domestic manufacturing information architecture
- industrial dark navigation
- production operations dashboard
- supply-chain risk overview
- AI Decision Center preview
- deterministic mock business data

Real manufacturing domain data and persistence are introduced in subsequent phases.
