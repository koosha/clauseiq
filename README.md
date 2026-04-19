# ClauseIQ

PrecedentIQ MVP — legal precedent retrieval for executed SaaS MSAs.

See [docs/architecture/PrecedentIQ_MVP_Plan_Consolidated.md](docs/architecture/PrecedentIQ_MVP_Plan_Consolidated.md) for the full design.
See [docs/architecture/PrecedentIQ_MVP_Ingestion_Plan.md](docs/architecture/PrecedentIQ_MVP_Ingestion_Plan.md) for the current ingestion implementation plan.
See [docs/README.md](docs/README.md) for the documentation layout.

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
