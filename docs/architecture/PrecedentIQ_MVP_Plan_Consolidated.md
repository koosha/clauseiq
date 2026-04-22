# PrecedentIQ MVP — Implementation Plan (Consolidated)

> This document supersedes the prior draft at [PrecedentIQ_MVP_Implementation_Plan.md](PrecedentIQ_MVP_Implementation_Plan.md). It preserves the scope and intent of that plan and locks in concrete technical choices that were previously unspecified or under-specified. Where this document and the prior draft conflict, **this document wins**.

---

## 1. Context

**Product goal.** Let a lawyer query a library of executed SaaS MSA contracts and retrieve the most relevant **clauses** (with citation back to their source contracts) for use in drafting.

**MVP scope.** Retrieval only. No UI, no auth, no multi-tenant, no drafting, no Word add-in. Single agreement type (SaaS MSA). Single version per contract.

**Success criterion.** Reliable retrieval quality, measured against a lawyer-curated gold set.

---

## 2. Executive Summary of Decisions

| # | Decision | Why |
|---|---|---|
| 1 | **OpenAI for all LLM + embeddings** | Single vendor, simpler ops, strong defaults. |
| 2 | **Embeddings: `text-embedding-3-large`** | 3072-dim; best OpenAI retrieval quality; cost acceptable for MVP corpus size. |
| 3 | **Classification: `gpt-5-mini`** | Best-balance mini model for structured 20-way classification. |
| 4 | **Reranker: `gpt-5-nano` as LLM-as-reranker** | Fastest/cheapest capable model for query-time reranking. |
| 5 | **Search engine: AWS OpenSearch Service (managed)** | Real BM25 + kNN in one managed service. Postgres holds only relational metadata. |
| 6 | **Fusion: Reciprocal Rank Fusion (RRF) with `k=60`** | Parameter-free, robust to score-scale mismatches, native OpenSearch support. |
| 7 | **Clause-only retrieval** | Drop `/search/contracts`. Every clause result carries full contract citation. |
| 8 | **Extraction: PyMuPDF + python-docx** | Layout-aware extraction that preserves structural markup for segmentation. |
| 9 | **Closed 20-family clause taxonomy** | See §7. Unclassifiable clauses stored with `family=null, confidence=low`. |
| 10 | **Gold set: 10 seed queries produced during MVP build; real gold set from user group later** | Enables eval harness from day one without blocking on user availability. |

---

## 3. Final Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Source files (DOCX + text PDF, in S3 or local FS)           │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Ingestion pipeline (Python + FastAPI worker)                │
│                                                             │
│  1. Extract     pymupdf (PDF) / python-docx (DOCX)          │
│                 Reject scanned PDFs with no text layer      │
│  2. Segment     Structure-aware (headings, numbering,       │
│                 defined-term protection)                    │
│  3. Classify    gpt-5-mini → clause_family (cached by       │
│                 clause checksum)                            │
│  4. Extract     Metadata: agreement_type, executed_status,  │
│                 governing_law, client, counterparty         │
│  5. Embed       text-embedding-3-large per clause           │
│  6. Persist     → Postgres (relational) + OpenSearch (index)│
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────┐    ┌─────────────────────────┐
│ PostgreSQL (RDS)             │    │ OpenSearch Service      │
│                              │    │                         │
│ contracts                    │    │ clauses index:          │
│ clauses (text + metadata)    │◄──►│  - clause_id (FK)       │
│ metadata_confidence          │    │  - text_normalized      │
│ gold_set                     │    │    (BM25 field)         │
│ eval_results                 │    │  - embedding (kNN vec)  │
│                              │    │  - filter fields:       │
│ (source of truth)            │    │    agreement_type,      │
│                              │    │    clause_family,       │
│                              │    │    governing_law        │
└──────────────────────────────┘    └─────────────────────────┘
                            ▲
                            │
┌─────────────────────────────────────────────────────────────┐
│ Retrieval API (FastAPI)                                     │
│                                                             │
│  POST /search/clauses    — hybrid BM25 + kNN + rerank       │
│  POST /search/by-text    — same pipeline, query is pasted   │
│                            clause text                      │
│                                                             │
│  Pipeline:                                                  │
│   1. Parse query → filters + query_text                     │
│   2. OpenSearch hybrid query:                               │
│        BM25 top-50  ──┐                                     │
│        kNN top-50   ──┤→ RRF fusion (native)  → top-100     │
│   3. gpt-5-nano reranks top-100 → top-20                    │
│   4. Metadata boosts (clause_family exact match,            │
│      governing_law match, etc.)                             │
│   5. Return top-k with full contract citation               │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
┌─────────────────────────────────────────────────────────────┐
│ Evaluation harness (CLI)                                    │
│                                                             │
│ Reads gold_set → runs queries → captures top-k ranked       │
│ results → computes Recall@k, Precision@k, MRR, nDCG         │
│ → writes eval_results with run_id + pipeline metadata       │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Component Choices (Detail)

### 4.1 Embeddings

- **Model:** OpenAI `text-embedding-3-large` (3072-dim).
- **Cost estimate:** ~$0.13 per 1M tokens. A corpus of 500 contracts × avg 30K tokens = 15M tokens = ~$2 to embed once.
- **Storage:** Vectors live in OpenSearch as `knn_vector` with cosine similarity. Also kept in Postgres as a blob for reproducibility (in case we re-index OpenSearch).
- **Versioning:** `embedding_model` and `embedding_version` columns on the `clauses` table (see §6).

### 4.2 Classification (clause family)

- **Model:** `gpt-5-mini` with JSON-schema structured output mode.
- **Taxonomy:** Closed list of 20 families (see §7).
- **Caching:** Keyed by clause checksum. Re-ingesting an unchanged clause costs nothing.
- **Fallback:** When the LLM returns `confidence=low` or can't assign a family, the ingester runs a secondary heading-keyword regex. If that also misses, we store `family=null, confidence=low, source=model_inference`.
- **Cost estimate:** ~10K clauses × ~300 tokens per call × `gpt-5-mini` pricing ≈ ~$20 one-time, cached.

### 4.3 Reranker

- **Model:** `gpt-5-nano` used as LLM-as-reranker.
- **Input:** Query + list of 100 candidate clauses (compressed to ~300 tokens each).
- **Output:** Relevance scores (0–10) per candidate in structured JSON.
- **Toggle:** Feature-flagged so the eval harness can measure quality delta with/without rerank.
- **Latency budget:** ≤1.5s added per query. Acceptable for MVP (no SLA requirement yet).
- **Cost estimate:** ~$0.002–0.005 per query.

### 4.4 Search engine

- **AWS OpenSearch Service (managed).**
- **Why not pgvector + ts_rank:** `ts_rank` is not BM25; quality leaves the table.
- **Why not ParadeDB:** `pg_search` extension is not on the RDS allowlist; self-hosting Postgres for this MVP is more ops than adding a managed OpenSearch cluster.
- **Why not split pgvector + OpenSearch:** Split-brain sync cost is not worth it for MVP. OpenSearch hybrid search (BM25 + kNN with built-in RRF) is one query.
- **Role of Postgres:** Source of truth for relational data (contracts, clauses, gold set, eval results). **No vectors in Postgres.** OpenSearch is eventually consistent with Postgres; ingestion writes to Postgres first, then pushes to OpenSearch.

### 4.5 Extraction

- **PDFs:** `pymupdf` (aka `fitz`). Preserves page numbers and rough layout. Reject scanned PDFs (no text layer) with a clear error. OCR deferred to post-MVP.
- **DOCX:** `python-docx`. Read heading styles and numbered-list structure — do **not** flatten to plaintext before segmentation.
- **Extraction version tracked** on the contract record (`extraction_tool`, `extraction_version`) so we can selectively re-ingest when the extractor changes.

### 4.6 Clause segmentation

- Structure-aware, not fixed-token windows.
- Signals used: heading style (Word), section numbering ("1.", "1.1", "(a)"), list indentation, heading keyword anchors.
- Defined-term protection: do not split inside a bolded/defined term boundary.
- Payment-style sub-clauses kept as separate records (invoicing timing, due date, disputed invoices, late fees, suspension) because lawyers often want one sub-part, not the whole section.

---

## 5. API Surface

### 5.1 Endpoints (MVP)

| Endpoint | Purpose |
|---|---|
| `POST /search/clauses` | Search clauses by natural-language query. |
| `POST /search/by-text` | Search clauses by pasted draft language (same pipeline, query text is the paste). |
| `POST /ingest` | Trigger ingestion of a file or folder (CLI-driven in MVP). |
| `POST /eval/run` | Run the gold set, write `eval_results` row, return metrics summary. |

### 5.2 Endpoints deliberately out of scope

- ~~`POST /search/contracts`~~ — dropped. Clause-level retrieval with contract citations covers the drafting workflow.
- Full-contract embeddings not generated.

### 5.3 Response shape (`POST /search/clauses`)

```json
{
  "query_id": "q_run_2026_04_19_001",
  "results": [
    {
      "clause_id": "cl_101",
      "score": 0.94,
      "text_display": "Customer shall pay all undisputed invoices within thirty (30) days of receipt...",
      "heading_text": "Payment Terms",
      "section_path": "Article 4 › Fees and Payment",
      "clause_family": "payment_terms",
      "confidence": "high",
      "contract": {
        "contract_id": "ctr_001",
        "title": "Acme SaaS Master Services Agreement",
        "source_filename": "Acme_MSA.pdf",
        "governing_law": "New York"
      },
      "highlights": ["undisputed invoices", "thirty (30) days"]
    }
  ],
  "debug": {
    "fused_from": {"bm25": 50, "knn": 50},
    "reranked": true,
    "filters_applied": {"agreement_type": ["SaaS_MSA"]}
  }
}
```

The `debug` block is present when `explain=true` is passed in the request; omitted otherwise.

---

## 6. Data Model

### 6.1 `contracts`

```json
{
  "contract_id": "string",
  "title": "string",
  "agreement_type": "SaaS_MSA",
  "executed_status": "executed",
  "governing_law": "string|null",
  "client_name": "string|null",
  "counterparty_name": "string|null",
  "source_file_path": "string",
  "source_filename": "string",
  "checksum_sha256": "string",
  "extraction_tool": "string",
  "extraction_version": "string",
  "ingest_status": "pending|parsed|embedded|indexed|failed",
  "created_at": "timestamp"
}
```

### 6.2 `clauses`

```json
{
  "clause_id": "string",
  "contract_id": "string",
  "section_path": "string|null",
  "heading_text": "string|null",
  "clause_family": "string|null",
  "text_display": "string",
  "text_normalized": "string",
  "char_start": "int|null",
  "char_end": "int|null",
  "embedding": "vector[3072]",
  "embedding_model": "string",
  "embedding_version": "string",
  "embedding_created_at": "timestamp",
  "language": "string",
  "jurisdiction": "string|null",
  "created_at": "timestamp"
}
```

### 6.3 `metadata_confidence`

```json
{
  "record_id": "string",
  "record_type": "contract|clause",
  "field_name": "string",
  "value": "string",
  "confidence": "high|medium|low",
  "source": "explicit_text|pattern|model_inference|manual"
}
```

Confidence is tracked only for: `agreement_type`, `executed_status`, `governing_law`, `clause_family`.

### 6.4 `gold_set`

```json
{
  "query_id": "string",
  "query_text": "string",
  "query_type": "clause|text_similarity",
  "filters_json": {},
  "expected_clause_ids": [],
  "split": "dev|test",
  "notes": "string|null",
  "created_by": "string",
  "created_at": "timestamp"
}
```

Queries are split 80/20 dev/test. **The test split is never examined during tuning.**

### 6.5 `eval_results`

```json
{
  "run_id": "string",
  "query_id": "string",
  "top_results_json": [],
  "metrics_json": {
    "recall_at_10": 0.0,
    "precision_at_10": 0.0,
    "mrr": 0.0,
    "ndcg_at_10": 0.0
  },
  "embedding_model": "string",
  "reranker_model": "string|null",
  "fusion_method": "rrf",
  "pipeline_git_sha": "string",
  "created_at": "timestamp"
}
```

---

## 7. Clause-Family Taxonomy (20 closed families)

| # | Family | Typical headings / signal |
|---|---|---|
| 1 | `definitions` | "Definitions", "Interpretation", "Certain Definitions" |
| 2 | `fees_and_pricing` | "Fees", "Pricing", "Subscription Fees", "Charges" |
| 3 | `payment_terms` | "Payment", "Invoicing", "Billing", "Taxes" |
| 4 | `late_payment_and_suspension` | "Late Payments", "Suspension", "Disputed Invoices" |
| 5 | `term_and_renewal` | "Term", "Renewal", "Auto-Renewal" |
| 6 | `termination` | "Termination", "Termination for Cause", "Survival" |
| 7 | `service_levels` | "Service Level Agreement", "Uptime", "SLA", "Availability" |
| 8 | `support_and_maintenance` | "Support", "Maintenance", "Updates", "Technical Support" |
| 9 | `data_security` | "Security", "Information Security", "Data Security" |
| 10 | `data_privacy` | "Privacy", "Data Processing", "Personal Data", "GDPR", "Sub-processors" |
| 11 | `confidentiality` | "Confidentiality", "Non-Disclosure" |
| 12 | `intellectual_property` | "Intellectual Property", "Ownership", "License", "Feedback" |
| 13 | `warranties_and_disclaimers` | "Warranties", "Representations and Warranties", "Disclaimer" |
| 14 | `limitation_of_liability` | "Limitation of Liability", "Liability Cap", "Exclusion of Damages" |
| 15 | `indemnification` | "Indemnification", "Indemnity", "IP Indemnification" |
| 16 | `insurance` | "Insurance", "Insurance Requirements" |
| 17 | `governing_law_and_jurisdiction` | "Governing Law", "Jurisdiction", "Venue" |
| 18 | `dispute_resolution` | "Dispute Resolution", "Arbitration", "Class Action Waiver" |
| 19 | `assignment_and_change_of_control` | "Assignment", "Change of Control", "Successors and Assigns" |
| 20 | `general_boilerplate` | "Notices", "Miscellaneous", "Force Majeure", "Entire Agreement", "Severability", "Waiver" |

### Design notes

- **No `other` bucket.** Unclassifiable clauses get `family=null, confidence=low`. They still participate in search; they just don't benefit from family-based filters or boosts.
- **`definitions` is default-excluded from search** unless the query explicitly targets it — definitions sections are often 20–40% of an MSA and would flood results.
- **Deliberately merged:** `late_fees`+`suspension`, `warranties`+`disclaimers`, `assignment`+`change_of_control`, `governing_law`+`jurisdiction` — each pair almost always appears together in a single clause.
- **Deliberately separate:** `service_levels` vs `support_and_maintenance`, `data_security` vs `data_privacy`, `warranties_and_disclaimers` vs `limitation_of_liability` — distinct lawyer search patterns despite surface similarity.

### Classification prompt shape

```
System: You classify clauses from executed SaaS Master Services Agreements into
one of 20 families. If no family clearly fits, return family=null with
confidence=low.

User: Given the following clause, return JSON with:
- family: one of [the 20 names above] or null
- confidence: high | medium | low
- rationale: one short sentence

HEADING: "{heading_text}"
SECTION PATH: "{section_path}"
CLAUSE TEXT:
{clause_text}
```

### Taxonomy validation step

After ingesting the first 5 contracts:
1. Look at family distribution — any family with zero hits, or any family >25% of total? Investigate.
2. Hand-check 30 random clauses — aim for ≥90% agreement with LLM assignment.
3. If a concept repeatedly hits `null`, promote it to a new family.

---

## 8. Retrieval Pipeline (Detail)

1. **Request parsing.** Split the incoming request into `query_text`, `filters`, and flags (`explain`, `top_k`, `with_reranker`).
2. **Structured filter application.** Applied as OpenSearch `filter` clauses — not scoring clauses — so filtered-out docs never reach the ranker.
3. **Hybrid candidate generation (single OpenSearch query).**
   - BM25 against `text_normalized` → top 50.
   - kNN against `embedding` → top 50.
   - Native OpenSearch hybrid query with RRF (`k=60`) → top 100.
4. **LLM rerank (gpt-5-nano).** If `with_reranker=true`, rerank top 100 → top 20. Otherwise skip.
5. **Metadata boosts.** Small multiplicative boosts for exact matches on `clause_family` and `governing_law` when the query implies them.
6. **Truncate to `top_k`** and return with full contract citation and optional `debug` block.

---

## 9. Gold Set & Evaluation

### 9.1 MVP seed gold set (produced during build)

I will generate **10 seed queries** across these categories:
- 3 × payment-related (clause search)
- 2 × limitation-of-liability (clause search)
- 2 × confidentiality (clause search)
- 1 × governing-law filter (clause search with filter)
- 1 × paste-and-match (text-similarity search)
- 1 × cross-cutting broad query

Each seed query has hand-labeled expected `clause_ids` drawn from the seed corpus. Split: 8 dev / 2 test.

### 9.2 Production gold set (post-MVP)

Comes from the user group (lawyers). Build protocol:
- 2-hour session: lawyer verbalizes 50 real queries.
- Pool-based labeling: for each query, pool the top-20 results from the current system; lawyer marks relevant / partial / not relevant.
- 80/20 split. **Test split is never touched during tuning.**

### 9.3 Metrics

- **Recall@k** (k ∈ {5, 10, 20})
- **Precision@k**
- **MRR**
- **nDCG@10** — primary metric
- **Per-family breakdown** — compute all metrics sliced by query's target `clause_family` so we can spot whether one family's quality is dragging the average.

### 9.4 Eval harness CLI

```
python -m app.eval.run --split dev --with-reranker true
# writes eval_results row, prints summary, writes per-query diff vs last run
```

---

## 10. Build Priority Order

1. Contract ingestion (file intake + checksum)
2. Text extraction (pymupdf + python-docx)
3. Clause segmentation
4. Metadata extraction + clause-family classification (gpt-5-mini)
5. Database schema (Postgres + OpenSearch index mapping)
6. Embeddings (text-embedding-3-large)
7. OpenSearch indexing (BM25 + kNN fields populated)
8. Clause search pipeline (hybrid + RRF + rerank)
9. Eval harness + 10 seed gold-set queries
10. Ranking tuning (metadata boost weights, reranker on/off)

---

## 11. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| **Clause segmentation fragility across counterparty formats** | Test on 5 contracts from 5 distinct sources before building downstream. Budget real time for this — it's the hidden cost sink. |
| **Contract PII / confidentiality during dev** | `.gitignore` for source contracts. Source files in S3 with bucket-level encryption. OpenAI API usage means text leaves the boundary — confirm this is acceptable for the corpus. |
| **Postgres ↔ OpenSearch sync drift** | Ingestion writes to Postgres first (source of truth), then pushes to OpenSearch. Nightly reconciliation job compares counts and checksums. |
| **Gold-set overfitting** | 80/20 split enforced at schema level; test split queries cannot be run during tuning. |
| **"Strong" / "favorable" judgment queries** | Accept degraded quality on these in MVP. Document the limitation. Can layer a dedicated "sentiment/strength" classifier in Phase 2 if real queries need it. |
| **One-version-per-contract assumption** | Ingestion rejects a contract whose `checksum_sha256` already exists. Re-ingestion requires explicit `--force` flag. |

---

## 12. Verification Plan

To validate this plan end-to-end before declaring Phase 1 done:

1. **Ingest seed corpus** of ~20 executed SaaS MSAs. Verify all land in Postgres + OpenSearch with correct counts.
2. **Run family-distribution check** on the seed corpus. Validate taxonomy holds up.
3. **Run all 10 seed gold-set queries** via `/search/clauses`. Eyeball top-10 for each.
4. **Run eval harness** on dev split. Record baseline nDCG@10.
5. **A/B the reranker** (with/without). Expect +10–25% relative nDCG@10 gain on legal text.
6. **Confirm test split** produces similar quality to dev split (if it diverges significantly, we overfit).
7. **Provenance spot-check:** pick 5 random results, follow `source_filename` + `section_path` back to the source contract, confirm they match.

---

## 13. Deferred to Post-MVP

Listed explicitly so they don't accidentally creep in:

- Authentication, RBAC, multi-tenant
- UI (any)
- Word add-in
- Automated draft generation
- Tracked changes / redlines
- DMS integrations
- Multiple versions per contract
- Contract-level ranking (add later if lawyer queries need it)
- Full-contract embeddings
- Scanned-PDF OCR
- Learning-to-rank (LambdaMART/XGBoost ranker trained on user feedback)
- Query intent classifier
- Query expansion / entity extraction

---

## 14. Appendix: Items Carried Forward from Prior Draft

These elements of [PrecedentIQ_MVP_Implementation_Plan.md](PrecedentIQ_MVP_Implementation_Plan.md) are unchanged and still apply:

- **Scope discipline** — §"In scope" / "Out of scope" (lines 11–37)
- **Three-level metadata confidence model** — lines 261–291
- **Provenance requirements** — lines 479–496
- **Clause segmentation rules** — lines 338–359
- **Phase 2 and Phase 3 deliverables** — lines 580–607
- **Repo layout** — lines 610–626
