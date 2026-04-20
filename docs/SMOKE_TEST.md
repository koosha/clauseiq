# Manual Smoke Test Checklist

This document describes how to validate the ingestion pipeline end-to-end against a real corpus of executed SaaS MSAs, a real Postgres + OpenSearch stack, and a real OpenAI API key.

The automated test suite (`uv run pytest`) already proves correctness of each unit and wires them together with mocks. This smoke test proves the pipeline works against real external services.

## Prerequisites

- Docker Desktop (or Docker Engine) running
- 3 or more executed SaaS MSA PDFs or DOCX files
- A valid OpenAI API key with access to `text-embedding-3-large` and `gpt-5-mini`
- Python 3.12+ and `uv` installed

## Procedure

### 1. Start local services

```bash
docker compose up -d
docker compose ps
```

Expected: both `postgres` and `opensearch` containers show `running` / `healthy`.

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
```

### 3. Apply database migrations

```bash
uv run alembic upgrade head
```

Expected: no errors. Verify with:

```bash
docker compose exec postgres psql -U clauseiq -d clauseiq -c "\dt"
```

Expected: three tables listed — `contracts`, `clauses`, `metadata_confidence`.

### 4. Initialize the OpenSearch index

```bash
uv run clauseiq init-index
```

Expected output: `ok`.

Verify with:

```bash
curl -s http://localhost:9200/clauses | python -m json.tool | head -20
```

Expected: index mapping returned, not a 404.

### 5. Place real contracts

```bash
mkdir -p contracts/source_files
# Copy 3 or more SaaS MSA PDFs or DOCX files into contracts/source_files/
ls contracts/source_files/
```

Note: `contracts/` is `.gitignore`d — real contracts must never be committed.

### 6. Ingest

```bash
uv run clauseiq ingest contracts/source_files/
```

Expected output: one `ingested <filename> -> ctr_xxx` line per contract.

### 7. Verify Postgres state

```bash
docker compose exec postgres psql -U clauseiq -d clauseiq \
  -c "SELECT contract_id, title, governing_law, ingest_status FROM contracts;"
```

Expected: every row has `ingest_status = 'indexed'` and `governing_law` populated where the contract clearly stated it.

```bash
docker compose exec postgres psql -U clauseiq -d clauseiq \
  -c "SELECT clause_family, COUNT(*) FROM clauses GROUP BY clause_family ORDER BY COUNT(*) DESC;"
```

Expected: clauses distributed across multiple families. No single family (other than possibly `definitions`) should hold more than ~25% of the total.

### 8. Verify OpenSearch state

```bash
curl -s "http://localhost:9200/clauses/_count" | python -m json.tool
```

Expected: `count` matches `SELECT COUNT(*) FROM clauses` in Postgres.

```bash
curl -s "http://localhost:9200/clauses/_search?size=1" | python -m json.tool
```

Expected: a sample document shows all fields, including a populated `embedding` array of length 3072.

### 9. Taxonomy accuracy spot-check

```bash
docker compose exec postgres psql -U clauseiq -d clauseiq -c "
SELECT clause_family, LEFT(text_display, 200)
FROM clauses
ORDER BY RANDOM()
LIMIT 30;
"
```

Manually review each row. Score each as correct / incorrect / ambiguous. Target: at least 27 of 30 correct. If a family is consistently wrong, record which one and file a follow-up issue.

### 10. Dedup check

Try to ingest one of the already-ingested files a second time:

```bash
uv run clauseiq ingest contracts/source_files/<one-already-ingested>.pdf
```

Expected output: `skip <filename>: Contract already ingested (checksum ...)`.

## Recording the Result

When the smoke test passes, create a short note at `docs/SMOKE_TEST_LOG.md` with:

- Date
- Number of contracts ingested
- Number of clauses indexed
- Top 5 clause families by count
- Taxonomy spot-check score (X of 30 correct)
- Any families that consistently misclassified

This log is useful context for later retrieval-quality work (Plan B) and for tuning the taxonomy.

## Troubleshooting

- **`alembic upgrade head` hangs** — Postgres is not yet ready. Wait 10 seconds, retry.
- **OpenSearch refuses connection** — the container can take ~30 seconds to become healthy. Wait and retry.
- **All clauses classified as `general_boilerplate`** — the LLM is being too conservative. Check that your OpenAI API key has access to `gpt-5-mini` and not an older model.
- **`embedding` field missing in OpenSearch** — the embedder returned an empty list; likely hitting a rate limit. Check OpenAI dashboard for 429s.
