# ADR 004 — PostgreSQL, Redis and Alembic foundation

Status: Accepted

## Context

FactoryPilot requires a durable transactional source of truth for manufacturing entities and a low-latency coordination layer for cache, locks and later event-stream workloads.

## Decision

Phase 0.5 standardizes the local data foundation on:

- PostgreSQL 18 as the primary transactional database.
- pgvector 0.8.6 installed in PostgreSQL for later grounded knowledge and embedding workloads.
- Redis 8 as the cache and coordination service.
- SQLAlchemy 2 async sessions with `asyncpg`.
- Alembic as the only database schema migration mechanism.
- Docker Compose for local PostgreSQL and Redis lifecycle.

The API remains independently startable. `/health/live` reports process liveness, while `/health/ready` validates PostgreSQL and Redis when their checks are enabled.

## Boundaries

PostgreSQL stores trusted business state. Redis must not become the system of record. Vector retrieval will use pgvector only for unstructured knowledge; orders, BOM, inventory, planning and quality state remain relational/domain data.

## Migration baseline

The first migration enables the `vector` extension. Domain tables are intentionally deferred to Phase 1 and Phase 2 so schema ownership follows the domain model rather than infrastructure bootstrap code.
