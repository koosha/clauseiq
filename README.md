# ClauseIQ

PrecedentIQ MVP — legal precedent retrieval for executed SaaS MSAs.

See [PrecedentIQ_MVP_Plan_Consolidated.md](PrecedentIQ_MVP_Plan_Consolidated.md) for the full design.
See [docs/superpowers/plans/](docs/superpowers/plans/) for the implementation plan.

## Quick Start

```bash
# Start Postgres + OpenSearch
docker compose up -d

# Install deps
uv sync --all-extras

# Apply migrations
uv run alembic upgrade head

# Initialize OpenSearch index
uv run clauseiq init-index

# Ingest a contract
uv run clauseiq ingest path/to/contract.pdf
```

## Development

```bash
uv run pytest              # run tests
uv run ruff check .        # lint
uv run mypy .              # type-check
```
