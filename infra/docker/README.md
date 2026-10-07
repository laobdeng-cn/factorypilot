# FactoryPilot local data infrastructure

Phase 0.5 introduces the persistent local data layer used by the FastAPI service.

## Services

- PostgreSQL 18 with pgvector 0.8.6
- Redis 8

## Start

From the repository root:

```powershell
docker compose up -d postgres redis
docker compose ps
```

## Stop

```powershell
docker compose stop postgres redis
```

## Remove containers only

```powershell
docker compose down
```

## Remove containers and local data

Use only when a full development reset is intended:

```powershell
docker compose down -v
```

PostgreSQL is exposed on `127.0.0.1:5432` and Redis on `127.0.0.1:6379` by default.
