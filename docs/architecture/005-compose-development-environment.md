# Phase 0.6 — Docker Compose Full Development Environment

## Decision

FactoryPilot provides a complete local container stack through the repository root `docker-compose.yml`.

The stack contains:

- `frontend`: Ant Design Pro / Umi development server
- `backend`: FastAPI application
- `postgres`: PostgreSQL 18 + pgvector
- `redis`: Redis 8

## Networking

All services join `factorypilot-network`.

Container-to-container traffic uses service DNS names:

- backend → PostgreSQL: `postgres:5432`
- backend → Redis: `redis:6379`
- frontend → backend proxy: `backend:8000`

Host mappings stay conflict-safe:

- frontend: `8001`
- backend: `8000`
- PostgreSQL: `55432`
- Redis: `56379`

## Startup Order

`backend` waits for PostgreSQL and Redis health checks before starting. It then applies `alembic upgrade head` before launching Uvicorn.

`frontend` waits for backend readiness before starting.

This makes `docker compose up -d --build` deterministic enough for Phase 0 development while keeping manual local development available.

## Scope

This phase containerizes the current engineering foundation only. Temporal, observability, simulator workers and Agent workers remain deferred to their planned phases.
