# ClauseIQ

A retrieval-first MVP for searching executed SaaS Master Services Agreements (MSAs). Given a natural-language query or a pasted clause, ClauseIQ returns the most relevant precedent clauses from a corpus of executed contracts, with full citation back to the source.

The goal is reliable retrieval quality for legal drafting workflows — not a full drafting system, document management platform, or multi-user product. Everything outside retrieval (authentication, UI, redlines, Word add-in) is deliberately out of scope for the MVP.

## Status

Active development. The ingestion pipeline is being built task-by-task against a written implementation plan.

Completed:

- Project scaffolding and typed configuration
- Database schema (contracts, clauses, metadata confidence) with Alembic migration
- OpenSearch index mapping (BM25 + 3072-dimension kNN vectors)
- File intake with SHA-256 deduplication
- PDF extraction (PyMuPDF) with scanned-PDF rejection
- DOCX extraction (python-docx) preserving heading structure
- Structure-aware clause segmentation
- Pattern-based contract metadata extraction with confidence tracking

In progress:

- Clause-family classifier (OpenAI `gpt-5-mini`, 20-family closed taxonomy)
- Embedder (OpenAI `text-embedding-3-large`)
- Postgres + OpenSearch persistence layer
- Ingestion orchestrator
- Click-based CLI
- End-to-end integration tests

## Stack

| Layer            | Technology                                                    |
| ---------------- | ------------------------------------------------------------- |
| Language         | Python 3.12+                                                  |
| Package manager  | uv                                                            |
| API framework    | FastAPI                                                       |
| Relational store | PostgreSQL 16 (source of truth)                               |
| Search engine    | OpenSearch 2.15 (BM25 + kNN)                                  |
| LLM              | OpenAI (`gpt-5-mini`, `gpt-5-nano`, `text-embedding-3-large`) |
| Migrations       | Alembic                                                       |
| ORM              | SQLAlchemy 2.0                                                |
| Tests            | pytest                                                        |
| Lint / types     | ruff, mypy                                                    |

## Prerequisites

- Python 3.12 or newer
- [uv](https://github.com/astral-sh/uv) for dependency management
- Docker (for local Postgres + OpenSearch)
- An OpenAI API key

## Getting Started

```bash
# 1. Install dependencies
uv sync --all-extras

# 2. Start Postgres and OpenSearch locally
docker compose up -d

# 3. Copy the example env and fill in your OpenAI key
cp .env.example .env
# edit .env and set OPENAI_API_KEY

# 4. Apply database migrations
uv run alembic upgrade head

# 5. Initialize the OpenSearch clauses index
uv run clauseiq init-index          # (available once the CLI ships)

# 6. Ingest a contract
uv run clauseiq ingest path/to/contract.pdf   # (available once the CLI ships)
```

## Development

```bash
uv run pytest                # run the test suite
uv run ruff check app tests  # lint
uv run mypy app              # type-check
```

Continuous integration runs the same three commands on every push and pull request against `main`.

## Project Structure

```text
clauseiq/
├── app/                       application code
│   ├── config.py              typed settings (pydantic-settings)
│   ├── db/                    SQLAlchemy models, session factory
│   ├── ingest/                ingestion pipeline
│   │   ├── extractors/        PDF and DOCX text extraction
│   │   ├── intake.py          file read + SHA-256 checksum
│   │   ├── segmenter.py       structure-aware clause segmentation
│   │   └── metadata.py        contract metadata extraction
│   └── search/                OpenSearch client and index mapping
├── alembic/                   database migrations
├── tests/                     pytest suite mirroring app/
│   └── fixtures/              sample PDF and DOCX for tests
├── docs/
│   ├── architecture/          MVP design and implementation plan
│   ├── design/                UI wireframes (placeholder)
│   └── research/              user research notes (placeholder)
├── docker-compose.yml         Postgres + OpenSearch for local dev
└── pyproject.toml             dependencies and tool configuration
```

## Configuration

All runtime configuration is loaded from environment variables via `pydantic-settings`. See [`.env.example`](.env.example) for the full list. The most important ones:

| Variable                  | Purpose                                       |
| ------------------------- | --------------------------------------------- |
| `DATABASE_URL`            | Postgres connection string                    |
| `OPENSEARCH_URL`          | OpenSearch endpoint                           |
| `OPENAI_API_KEY`          | Required for embedding and classification     |
| `OPENAI_EMBEDDING_MODEL`  | Default `text-embedding-3-large` (3072-dim)   |
| `OPENAI_CLASSIFIER_MODEL` | Default `gpt-5-mini`                          |
| `OPENAI_RERANKER_MODEL`   | Default `gpt-5-nano`                          |

## Design Documents

- [`docs/architecture/PrecedentIQ_MVP_Plan_Consolidated.md`](docs/architecture/PrecedentIQ_MVP_Plan_Consolidated.md) — full product and architectural design, with the rationale behind each technical choice.
- [`docs/architecture/PrecedentIQ_MVP_Ingestion_Plan.md`](docs/architecture/PrecedentIQ_MVP_Ingestion_Plan.md) — task-by-task implementation plan for the ingestion pipeline.
- [`docs/README.md`](docs/README.md) — documentation layout.

## Out of Scope (MVP)

Deliberately deferred so the MVP stays focused on retrieval quality:

- Authentication, RBAC, multi-tenancy
- Web or desktop UI of any kind
- Microsoft Word add-in
- Automated draft assembly, tracked changes, redlines
- DMS integrations
- Multiple versions per executed contract
- Scanned-PDF OCR
- Contract-level ranking (handled implicitly via clause-level hits with provenance)

## License

Not yet licensed. All rights reserved by the author until a license is chosen.
