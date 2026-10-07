# Phase 0.7 — CI and Code Quality

## Decision

FactoryPilot uses GitHub Actions as the repository quality gate for pushes and pull requests targeting `main`.

## CI jobs

### Backend Quality

Runs on Python 3.13 and executes:

1. `uv sync`
2. `uv run ruff check .`
3. `uv run mypy app`
4. `uv run pytest`

The current backend test suite is intentionally infrastructure-independent. Database integration tests will receive dedicated PostgreSQL/Redis services when manufacturing domain persistence is introduced.

### Frontend Quality

Runs on Node.js 22 with pnpm 10.17.1 and executes:

1. `pnpm install --no-frozen-lockfile`
2. `pnpm lint:web`
3. `pnpm typecheck:web`
4. `pnpm test:web`
5. `pnpm build:web`

`--no-frozen-lockfile` is temporary because the generated lockfiles have not yet been committed. Once lockfiles are version controlled, CI will switch to frozen/reproducible installation.

### Compose Validation

Runs `docker compose config --quiet` to reject invalid Compose configuration before merge.

## Dependency monitoring

Dependabot checks npm workspace dependencies and Python backend dependencies weekly. Dependency pull requests are not auto-merged.

## Policy

A change is considered merge-ready only when all relevant CI jobs pass. As later phases add integration tests, Agent evaluation and container smoke tests, they will be appended as separate quality gates rather than folded into a single opaque job.
