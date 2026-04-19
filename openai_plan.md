# ClauseIQ Bootstrap And First Runnable Slice

## Summary

Bring the repo from "design docs + scaffold" to a truthful, runnable ingestion foundation. The first milestone should make the documented local workflow real, keep docs aligned with reality, and deliver one end-to-end ingest path for local PDF/DOCX files into Postgres and OpenSearch without depending on live OpenAI calls in tests.

## Findings Summary

1. The packaged CLI is currently broken because `pyproject.toml` declares `clauseiq = "app.cli:cli"` but `app/cli.py` does not exist.
2. The README documents commands and infrastructure that the repo does not yet implement, including `docker compose`, Alembic migrations, and CLI commands.
3. The repo is effectively scaffold-only today: `pytest` collects no tests, and the current `mypy` success only reflects that there are almost no source files yet.
4. The architecture and ingestion plan are well specified in docs, but the implementation has not started beyond bootstrap files.
5. Python version targeting should be normalized early to avoid drift between the declared 3.12 target and the current local 3.13 environment.

## Key Changes

- Make the advertised interface real:
  - Add a working `app.cli` entrypoint for `clauseiq`.
  - Support `clauseiq init-index` and `clauseiq ingest <path>` as the first public commands because they are already documented.
  - Add `app.config` and `app.logging` so CLI startup, env loading, and error messages are consistent.

- Add the minimum local infrastructure the README promises:
  - Create `docker-compose.yml` for Postgres + OpenSearch.
  - Add Alembic config and an initial migration.
  - Keep the README limited to commands that are actually implemented and verified.

- Implement the first ingestion vertical slice:
  - Add DB models and persistence for `contracts`, `clauses`, and `metadata_confidence`.
  - Add OpenSearch client + index mapping for the clauses index.
  - Add PDF/DOCX extraction, scanned-PDF rejection, deterministic clause segmentation, and basic metadata extraction.
  - Add classifier and embedder interfaces with injectable implementations so production can use OpenAI later, while tests use local fakes.

- Keep scope intentionally narrow for this phase:
  - Do not implement FastAPI search endpoints yet.
  - Do not implement live reranking or evaluation harness yet.
  - Do implement enough persistence and indexing so search can be built on a stable substrate next.

## Public Interfaces And Behavior

- CLI:
  - `clauseiq init-index`
  - `clauseiq ingest <file-or-directory>`
  - `clauseiq --help` must work from a clean checkout after setup

- Configuration via environment:
  - `DATABASE_URL`
  - `OPENSEARCH_URL`, `OPENSEARCH_USER`, `OPENSEARCH_PASSWORD`, `OPENSEARCH_CLAUSES_INDEX`
  - `OPENAI_API_KEY`
  - `OPENAI_EMBEDDING_MODEL`, `OPENAI_EMBEDDING_DIM`, `OPENAI_CLASSIFIER_MODEL`
  - `LOG_LEVEL`, `CONTRACTS_DIR`

- Persistence contract:
  - Postgres is the source of truth for contracts and clauses.
  - OpenSearch is a derived index populated from persisted clause records.
  - Ingest should be idempotent by source checksum so re-running on the same file does not duplicate rows.

## Test Plan

- Bootstrap checks:
  - `uv run clauseiq --help` executes without import errors.
  - `uv run pytest` collects real tests.
  - `uv run mypy .` passes on implemented modules.
  - `uv run ruff check .` passes once command access is available.

- Unit scenarios:
  - Config fails clearly when required env vars are missing.
  - PDF extractor rejects a scanned PDF with no text layer.
  - DOCX/PDF extraction preserves enough structure for segmentation.
  - Segmenter produces stable clause boundaries on fixture documents.
  - `init-index` is safe to run repeatedly.
  - Duplicate ingest of the same file is idempotent.

- Integration scenario:
  - With local Postgres + OpenSearch running, ingesting a fixture document creates one contract record, multiple clause records, and matching OpenSearch documents.

## Assumptions And Defaults

- Python 3.12 is the canonical target for local dev and CI; 3.13 compatibility is deferred unless explicitly adopted.
- README accuracy takes priority over aspirational documentation; anything not implemented should be removed from Quick Start until it exists.
- OpenAI-backed classification and embeddings will be wrapped behind interfaces and excluded from CI by using deterministic fakes.
- The immediate next milestone after this one is retrieval/search, not UI, auth, or multi-tenancy.
