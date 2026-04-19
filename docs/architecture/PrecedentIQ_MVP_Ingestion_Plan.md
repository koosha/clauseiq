# PrecedentIQ MVP — Ingestion Plan (Plan A of 3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete ingestion pipeline that takes an executed SaaS MSA (PDF/DOCX), extracts text, segments it into clauses, extracts metadata, classifies clause families, generates embeddings, and persists everything to Postgres + OpenSearch.

**Architecture:** A Python/FastAPI service with a CLI entry point. Each ingestion stage is a pure function in its own module, orchestrated by `app/ingest/orchestrator.py`. Postgres is the source of truth; OpenSearch is a derived search index. Follows TDD; every module has a test before implementation.

**Tech Stack:** Python 3.12, uv for dependency management, SQLAlchemy 2.0 + Alembic, psycopg (Postgres driver), opensearch-py, PyMuPDF, python-docx, OpenAI SDK v1.x, pytest, testcontainers-python for integration tests.

**Reference:** All decisions in [../../../PrecedentIQ_MVP_Plan_Consolidated.md](../../../PrecedentIQ_MVP_Plan_Consolidated.md).

---

## File Structure

```
clauseiq/
├── .env.example
├── .gitignore
├── pyproject.toml
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 0001_initial_schema.py
├── app/
│   ├── __init__.py
│   ├── config.py                       # env-var config (pydantic-settings)
│   ├── cli.py                          # Click-based CLI
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py                   # SQLAlchemy models
│   │   └── session.py                  # session factory
│   ├── search/
│   │   ├── __init__.py
│   │   ├── client.py                   # OpenSearch client factory
│   │   └── index_mapping.py            # index schema for clauses index
│   ├── ingest/
│   │   ├── __init__.py
│   │   ├── intake.py                   # file read + checksum + dedup check
│   │   ├── extractors/
│   │   │   ├── __init__.py
│   │   │   ├── pdf.py                  # PyMuPDF wrapper
│   │   │   └── docx.py                 # python-docx wrapper
│   │   ├── segmenter.py                # clause boundary detection
│   │   ├── metadata.py                 # extract governing_law, parties, etc.
│   │   ├── taxonomy.py                 # 20-family enum + prompt template
│   │   ├── classifier.py               # OpenAI gpt-5-mini wrapper
│   │   ├── embedder.py                 # OpenAI text-embedding-3-large wrapper
│   │   ├── persistence.py              # write to Postgres + OpenSearch
│   │   └── orchestrator.py             # wires the stages together
│   └── logging.py                      # structlog config
├── tests/
│   ├── __init__.py
│   ├── conftest.py                     # pytest fixtures (DB, OpenSearch)
│   ├── fixtures/
│   │   ├── sample.pdf                  # small hand-crafted test PDF
│   │   ├── sample.docx                 # small hand-crafted test DOCX
│   │   └── scanned.pdf                 # PDF with no text layer (for reject test)
│   ├── db/
│   │   └── test_models.py
│   ├── search/
│   │   └── test_index_setup.py
│   ├── ingest/
│   │   ├── test_intake.py
│   │   ├── extractors/
│   │   │   ├── test_pdf.py
│   │   │   └── test_docx.py
│   │   ├── test_segmenter.py
│   │   ├── test_metadata.py
│   │   ├── test_classifier.py
│   │   ├── test_embedder.py
│   │   ├── test_persistence.py
│   │   └── test_orchestrator.py
│   └── integration/
│       └── test_ingest_e2e.py
└── docker-compose.yml                  # local Postgres + OpenSearch for dev
```

Every file above has a single responsibility. The ingestion stages chain together via the orchestrator with clear hand-off types.

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `README.md`
- Create: `app/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1.1: Initialize git**

Run:
```bash
cd "/Users/mb16/My Drive (koosha.g@gmail.com)/code/clauseiq"
git init
git branch -m main
```

Expected: `Initialized empty Git repository...`

- [ ] **Step 1.2: Install uv if missing**

Run:
```bash
which uv || curl -LsSf https://astral.sh/uv/install.sh | sh
```

- [ ] **Step 1.3: Create `pyproject.toml`**

```toml
[project]
name = "clauseiq"
version = "0.1.0"
description = "PrecedentIQ MVP — legal precedent retrieval for SaaS MSAs"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn>=0.30",
    "sqlalchemy>=2.0",
    "alembic>=1.13",
    "psycopg[binary]>=3.2",
    "pydantic>=2.7",
    "pydantic-settings>=2.3",
    "opensearch-py>=2.6",
    "pymupdf>=1.24",
    "python-docx>=1.1",
    "openai>=1.40",
    "click>=8.1",
    "structlog>=24.1",
    "tenacity>=8.3",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2",
    "pytest-asyncio>=0.23",
    "testcontainers[postgres,opensearch]>=4.8",
    "ruff>=0.5",
    "mypy>=1.10",
]

[project.scripts]
clauseiq = "app.cli:cli"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.mypy]
python_version = "3.12"
strict = true

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 1.4: Create `.gitignore`**

```
# Python
__pycache__/
*.py[cod]
.venv/
*.egg-info/

# Contracts (NEVER commit source contracts)
contracts/
tests/fixtures/*.pdf
tests/fixtures/*.docx
!tests/fixtures/sample.pdf
!tests/fixtures/sample.docx
!tests/fixtures/scanned.pdf

# Env
.env
.env.local

# IDE
.vscode/
.idea/

# OS
.DS_Store

# Logs
*.log
```

- [ ] **Step 1.5: Create `.env.example`**

```
# Postgres
DATABASE_URL=postgresql+psycopg://clauseiq:clauseiq@localhost:5432/clauseiq

# OpenSearch
OPENSEARCH_URL=http://localhost:9200
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD=admin
OPENSEARCH_CLAUSES_INDEX=clauses

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_EMBEDDING_DIM=3072
OPENAI_CLASSIFIER_MODEL=gpt-5-mini
OPENAI_RERANKER_MODEL=gpt-5-nano

# App
LOG_LEVEL=INFO
CONTRACTS_DIR=./contracts/source_files
```

- [ ] **Step 1.6: Create empty package markers**

```bash
touch app/__init__.py tests/__init__.py
```

- [ ] **Step 1.7: Install dependencies**

Run:
```bash
uv sync --all-extras
```

Expected: `.venv/` created, dependencies resolved.

- [ ] **Step 1.8: Commit**

```bash
git add pyproject.toml .gitignore .env.example app/__init__.py tests/__init__.py
git commit -m "chore: project scaffolding with uv + pyproject.toml"
```

---

## Task 2: Configuration Module

**Files:**
- Create: `app/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 2.1: Write failing test `tests/test_config.py`**

```python
import os
import pytest
from app.config import Settings


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@h:5432/d")
    monkeypatch.setenv("OPENSEARCH_URL", "http://localhost:9200")
    monkeypatch.setenv("OPENSEARCH_USER", "admin")
    monkeypatch.setenv("OPENSEARCH_PASSWORD", "admin")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    s = Settings()

    assert s.database_url == "postgresql+psycopg://u:p@h:5432/d"
    assert s.openai_embedding_model == "text-embedding-3-large"
    assert s.openai_embedding_dim == 3072
    assert s.openai_classifier_model == "gpt-5-mini"
    assert s.openai_reranker_model == "gpt-5-nano"
    assert s.opensearch_clauses_index == "clauses"


def test_settings_rejects_missing_required(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(Exception):
        Settings()
```

- [ ] **Step 2.2: Run test — expect FAIL**

Run: `uv run pytest tests/test_config.py -v`
Expected: `ModuleNotFoundError: No module named 'app.config'`

- [ ] **Step 2.3: Implement `app/config.py`**

```python
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    opensearch_url: str = "http://localhost:9200"
    opensearch_user: str = "admin"
    opensearch_password: str = "admin"
    opensearch_clauses_index: str = "clauses"

    openai_api_key: str
    openai_embedding_model: str = "text-embedding-3-large"
    openai_embedding_dim: int = 3072
    openai_classifier_model: str = "gpt-5-mini"
    openai_reranker_model: str = "gpt-5-nano"

    log_level: str = "INFO"
    contracts_dir: str = "./contracts/source_files"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 2.4: Run test — expect PASS**

Run: `uv run pytest tests/test_config.py -v`
Expected: `2 passed`

- [ ] **Step 2.5: Commit**

```bash
git add app/config.py tests/test_config.py
git commit -m "feat(config): typed settings via pydantic-settings"
```

---

## Task 3: Database Models

**Files:**
- Create: `app/db/__init__.py`
- Create: `app/db/session.py`
- Create: `app/db/models.py`
- Test: `tests/db/test_models.py`

- [ ] **Step 3.1: Write failing test `tests/db/test_models.py`**

```python
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.models import Base, Contract, Clause, MetadataConfidence


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_contract_roundtrip(session):
    c = Contract(
        contract_id="ctr_001",
        title="Acme MSA",
        agreement_type="SaaS_MSA",
        executed_status="executed",
        governing_law="New York",
        source_filename="Acme_MSA.pdf",
        source_file_path="/tmp/Acme_MSA.pdf",
        checksum_sha256="abc123",
        extraction_tool="pymupdf",
        extraction_version="1.24",
        ingest_status="pending",
        created_at=datetime.now(timezone.utc),
    )
    session.add(c)
    session.commit()
    loaded = session.get(Contract, "ctr_001")
    assert loaded.title == "Acme MSA"


def test_clause_links_to_contract(session):
    c = Contract(
        contract_id="ctr_002",
        title="X",
        agreement_type="SaaS_MSA",
        executed_status="executed",
        source_filename="x.pdf",
        source_file_path="/tmp/x.pdf",
        checksum_sha256="def456",
        extraction_tool="pymupdf",
        extraction_version="1.24",
        ingest_status="pending",
        created_at=datetime.now(timezone.utc),
    )
    session.add(c)
    session.flush()

    cl = Clause(
        clause_id="cl_001",
        contract_id="ctr_002",
        text_display="Customer shall pay...",
        text_normalized="customer shall pay",
        clause_family="payment_terms",
        embedding_model="text-embedding-3-large",
        embedding_version="2024-01",
        embedding_created_at=datetime.now(timezone.utc),
        language="en",
        created_at=datetime.now(timezone.utc),
    )
    session.add(cl)
    session.commit()
    assert session.get(Clause, "cl_001").contract_id == "ctr_002"
```

- [ ] **Step 3.2: Run test — expect FAIL**

Run: `uv run pytest tests/db/test_models.py -v`
Expected: `ModuleNotFoundError: No module named 'app.db.models'`

- [ ] **Step 3.3: Implement `app/db/models.py`**

```python
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Integer, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Contract(Base):
    __tablename__ = "contracts"

    contract_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(512))
    agreement_type: Mapped[str] = mapped_column(String(64))
    executed_status: Mapped[str] = mapped_column(String(32))
    governing_law: Mapped[str | None] = mapped_column(String(128), nullable=True)
    client_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    counterparty_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    source_file_path: Mapped[str] = mapped_column(Text)
    source_filename: Mapped[str] = mapped_column(String(512))
    checksum_sha256: Mapped[str] = mapped_column(String(64), unique=True)
    extraction_tool: Mapped[str] = mapped_column(String(64))
    extraction_version: Mapped[str] = mapped_column(String(32))
    ingest_status: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    clauses: Mapped[list["Clause"]] = relationship(back_populates="contract")


class Clause(Base):
    __tablename__ = "clauses"

    clause_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.contract_id"))
    section_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    heading_text: Mapped[str | None] = mapped_column(String(512), nullable=True)
    clause_family: Mapped[str | None] = mapped_column(String(64), nullable=True)
    text_display: Mapped[str] = mapped_column(Text)
    text_normalized: Mapped[str] = mapped_column(Text)
    char_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    embedding_model: Mapped[str] = mapped_column(String(64))
    embedding_version: Mapped[str] = mapped_column(String(32))
    embedding_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    language: Mapped[str] = mapped_column(String(8))
    jurisdiction: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    contract: Mapped["Contract"] = relationship(back_populates="clauses")


class MetadataConfidence(Base):
    __tablename__ = "metadata_confidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_id: Mapped[str] = mapped_column(String(64))
    record_type: Mapped[str] = mapped_column(String(16))
    field_name: Mapped[str] = mapped_column(String(64))
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[str] = mapped_column(String(16))
    source: Mapped[str] = mapped_column(String(32))
```

- [ ] **Step 3.4: Implement `app/db/session.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import get_settings


def make_session_factory() -> sessionmaker[Session]:
    engine = create_engine(get_settings().database_url, echo=False)
    return sessionmaker(engine, expire_on_commit=False)
```

- [ ] **Step 3.5: Create `app/db/__init__.py`**

```python
from app.db.models import Base, Contract, Clause, MetadataConfidence
from app.db.session import make_session_factory

__all__ = ["Base", "Contract", "Clause", "MetadataConfidence", "make_session_factory"]
```

- [ ] **Step 3.6: Create `tests/db/__init__.py`**

```bash
touch tests/db/__init__.py
```

- [ ] **Step 3.7: Run test — expect PASS**

Run: `uv run pytest tests/db/test_models.py -v`
Expected: `2 passed`

- [ ] **Step 3.8: Commit**

```bash
git add app/db/ tests/db/
git commit -m "feat(db): SQLAlchemy models for contract, clause, metadata_confidence"
```

---

## Task 4: Alembic Migration

**Files:**
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/script.py.mako`
- Create: `alembic/versions/0001_initial_schema.py`
- Create: `docker-compose.yml`

- [ ] **Step 4.1: Create `docker-compose.yml` for local Postgres + OpenSearch**

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: clauseiq
      POSTGRES_PASSWORD: clauseiq
      POSTGRES_DB: clauseiq
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data

  opensearch:
    image: opensearchproject/opensearch:2.15.0
    environment:
      - discovery.type=single-node
      - plugins.security.disabled=true
      - "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g"
    ports:
      - "9200:9200"
    ulimits:
      memlock:
        soft: -1
        hard: -1

volumes:
  pg_data:
```

- [ ] **Step 4.2: Start services**

Run:
```bash
docker compose up -d
```

Expected: both containers healthy. Verify with `docker compose ps`.

- [ ] **Step 4.3: Init alembic**

Run:
```bash
uv run alembic init alembic
```

- [ ] **Step 4.4: Edit `alembic.ini` — set sqlalchemy.url**

Change the line:
```
sqlalchemy.url = driver://user:pass@localhost/dbname
```
to:
```
# sqlalchemy.url is set dynamically in env.py
```

- [ ] **Step 4.5: Replace `alembic/env.py` contents**

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.config import get_settings
from app.db.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
```

- [ ] **Step 4.6: Generate initial migration**

Run:
```bash
uv run alembic revision --autogenerate -m "initial schema"
```

Expected: a new file `alembic/versions/<hash>_initial_schema.py` is created. Rename it to `0001_initial_schema.py` and manually set `revision = "0001"`.

- [ ] **Step 4.7: Apply migration**

Run:
```bash
uv run alembic upgrade head
```

Expected: tables `contracts`, `clauses`, `metadata_confidence` exist in Postgres.

Verify:
```bash
docker compose exec postgres psql -U clauseiq -d clauseiq -c "\dt"
```

Expected: three user tables listed.

- [ ] **Step 4.8: Commit**

```bash
git add alembic.ini alembic/ docker-compose.yml
git commit -m "feat(db): alembic initial migration + docker-compose for local dev"
```

---

## Task 5: OpenSearch Index Setup

**Files:**
- Create: `app/search/__init__.py`
- Create: `app/search/client.py`
- Create: `app/search/index_mapping.py`
- Test: `tests/search/test_index_setup.py`

- [ ] **Step 5.1: Write failing test `tests/search/test_index_setup.py`**

```python
import pytest
from app.search.client import make_client
from app.search.index_mapping import CLAUSES_INDEX_BODY, ensure_clauses_index
from app.config import get_settings


@pytest.fixture()
def client():
    c = make_client()
    yield c
    c.indices.delete(index=get_settings().opensearch_clauses_index, ignore=[404])


def test_ensure_clauses_index_creates_expected_mapping(client):
    ensure_clauses_index(client)
    idx = get_settings().opensearch_clauses_index
    assert client.indices.exists(index=idx)
    mapping = client.indices.get_mapping(index=idx)[idx]["mappings"]["properties"]
    assert mapping["text_normalized"]["type"] == "text"
    assert mapping["embedding"]["type"] == "knn_vector"
    assert mapping["embedding"]["dimension"] == 3072
    assert mapping["clause_family"]["type"] == "keyword"
    assert mapping["contract_id"]["type"] == "keyword"
```

- [ ] **Step 5.2: Run test — expect FAIL**

Run: `uv run pytest tests/search/test_index_setup.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 5.3: Implement `app/search/client.py`**

```python
from opensearchpy import OpenSearch
from app.config import get_settings


def make_client() -> OpenSearch:
    s = get_settings()
    return OpenSearch(
        hosts=[s.opensearch_url],
        http_auth=(s.opensearch_user, s.opensearch_password),
        use_ssl=s.opensearch_url.startswith("https"),
        verify_certs=False,
        ssl_show_warn=False,
    )
```

- [ ] **Step 5.4: Implement `app/search/index_mapping.py`**

```python
from opensearchpy import OpenSearch
from app.config import get_settings


CLAUSES_INDEX_BODY = {
    "settings": {
        "index": {
            "knn": True,
            "knn.algo_param.ef_search": 100,
        },
        "analysis": {
            "analyzer": {
                "legal_english": {
                    "type": "standard",
                    "stopwords": "_english_",
                }
            }
        },
    },
    "mappings": {
        "properties": {
            "clause_id": {"type": "keyword"},
            "contract_id": {"type": "keyword"},
            "agreement_type": {"type": "keyword"},
            "clause_family": {"type": "keyword"},
            "governing_law": {"type": "keyword"},
            "jurisdiction": {"type": "keyword"},
            "section_path": {"type": "text"},
            "heading_text": {"type": "text"},
            "text_display": {"type": "text", "analyzer": "legal_english"},
            "text_normalized": {
                "type": "text",
                "analyzer": "legal_english",
                "similarity": "BM25",
            },
            "embedding": {
                "type": "knn_vector",
                "dimension": 3072,
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "lucene",
                    "parameters": {"ef_construction": 128, "m": 16},
                },
            },
        }
    },
}


def ensure_clauses_index(client: OpenSearch) -> None:
    idx = get_settings().opensearch_clauses_index
    if not client.indices.exists(index=idx):
        client.indices.create(index=idx, body=CLAUSES_INDEX_BODY)
```

- [ ] **Step 5.5: Create package markers**

```bash
touch app/search/__init__.py tests/search/__init__.py
```

- [ ] **Step 5.6: Run test — expect PASS**

Run: `uv run pytest tests/search/test_index_setup.py -v`
Expected: `1 passed`

- [ ] **Step 5.7: Commit**

```bash
git add app/search/ tests/search/
git commit -m "feat(search): opensearch client + clauses index mapping"
```

---

## Task 6: File Intake & Checksum

**Files:**
- Create: `app/ingest/__init__.py`
- Create: `app/ingest/intake.py`
- Create: `tests/ingest/__init__.py`
- Create: `tests/ingest/test_intake.py`

- [ ] **Step 6.1: Write failing test `tests/ingest/test_intake.py`**

```python
from pathlib import Path
from app.ingest.intake import intake_file, IntakeResult


def test_intake_produces_checksum_and_metadata(tmp_path: Path):
    f = tmp_path / "sample.pdf"
    f.write_bytes(b"%PDF-1.4 minimal contents")

    result: IntakeResult = intake_file(f)

    assert result.checksum_sha256 is not None
    assert len(result.checksum_sha256) == 64
    assert result.source_filename == "sample.pdf"
    assert result.source_file_path == str(f)
    assert result.file_extension == ".pdf"


def test_intake_detects_docx(tmp_path: Path):
    f = tmp_path / "X.docx"
    f.write_bytes(b"PK\x03\x04 fake zip")
    result = intake_file(f)
    assert result.file_extension == ".docx"


def test_intake_rejects_unsupported_extension(tmp_path: Path):
    import pytest
    f = tmp_path / "notes.txt"
    f.write_text("hello")
    with pytest.raises(ValueError, match="Unsupported file type"):
        intake_file(f)
```

- [ ] **Step 6.2: Run test — expect FAIL**

Run: `uv run pytest tests/ingest/test_intake.py -v`
Expected: import error.

- [ ] **Step 6.3: Implement `app/ingest/intake.py`**

```python
import hashlib
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


@dataclass(frozen=True)
class IntakeResult:
    source_filename: str
    source_file_path: str
    file_extension: str
    checksum_sha256: str
    size_bytes: int


def intake_file(path: Path) -> IntakeResult:
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")

    data = path.read_bytes()
    return IntakeResult(
        source_filename=path.name,
        source_file_path=str(path),
        file_extension=ext,
        checksum_sha256=hashlib.sha256(data).hexdigest(),
        size_bytes=len(data),
    )
```

- [ ] **Step 6.4: Create package markers**

```bash
touch app/ingest/__init__.py tests/ingest/__init__.py
```

- [ ] **Step 6.5: Run test — expect PASS**

Run: `uv run pytest tests/ingest/test_intake.py -v`
Expected: `3 passed`

- [ ] **Step 6.6: Commit**

```bash
git add app/ingest/intake.py app/ingest/__init__.py tests/ingest/test_intake.py tests/ingest/__init__.py
git commit -m "feat(ingest): file intake with sha256 checksum"
```

---

## Task 7: PDF Extractor

**Files:**
- Create: `app/ingest/extractors/__init__.py`
- Create: `app/ingest/extractors/pdf.py`
- Create: `tests/ingest/extractors/__init__.py`
- Create: `tests/ingest/extractors/test_pdf.py`
- Create: `tests/fixtures/sample.pdf` (small hand-crafted PDF with 2 sections)
- Create: `tests/fixtures/scanned.pdf` (PDF with only an image, no text layer)

- [ ] **Step 7.1: Generate test fixture PDFs**

Run this one-off script to create fixtures:
```bash
uv run python -c '
import fitz
doc = fitz.open()
page = doc.new_page()
page.insert_text((72, 72), "1. Definitions\n\n\"Services\" means the cloud-based software offering.\n\n2. Payment Terms\n\nCustomer shall pay all undisputed invoices within thirty (30) days.", fontsize=11)
doc.save("tests/fixtures/sample.pdf")
doc.close()

# scanned PDF: image-only, no text layer
doc2 = fitz.open()
p2 = doc2.new_page()
pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 100, 100))
pix.clear_with(255)
p2.insert_image(fitz.Rect(0, 0, 100, 100), pixmap=pix)
doc2.save("tests/fixtures/scanned.pdf")
doc2.close()
'
```

Verify files exist:
```bash
ls -la tests/fixtures/
```

- [ ] **Step 7.2: Write failing test `tests/ingest/extractors/test_pdf.py`**

```python
from pathlib import Path
import pytest
from app.ingest.extractors.pdf import extract_pdf, PdfExtractionError


FIXTURES = Path(__file__).parent.parent.parent / "fixtures"


def test_extract_pdf_returns_text_and_page_offsets():
    result = extract_pdf(FIXTURES / "sample.pdf")
    assert "Payment Terms" in result.text
    assert "undisputed invoices" in result.text
    assert result.page_count == 1
    assert result.extraction_tool == "pymupdf"


def test_extract_pdf_rejects_scanned():
    with pytest.raises(PdfExtractionError, match="no text layer"):
        extract_pdf(FIXTURES / "scanned.pdf")
```

- [ ] **Step 7.3: Run test — expect FAIL**

Run: `uv run pytest tests/ingest/extractors/test_pdf.py -v`
Expected: module import error.

- [ ] **Step 7.4: Implement `app/ingest/extractors/pdf.py`**

```python
from dataclasses import dataclass
from pathlib import Path
import fitz  # PyMuPDF


class PdfExtractionError(Exception):
    pass


@dataclass(frozen=True)
class PdfExtractionResult:
    text: str
    page_count: int
    page_offsets: list[int]  # character offset where each page starts
    extraction_tool: str
    extraction_version: str


MIN_TEXT_CHARS_PER_PAGE = 50


def extract_pdf(path: Path) -> PdfExtractionResult:
    doc = fitz.open(path)
    try:
        pages: list[str] = []
        offsets: list[int] = []
        total_chars = 0

        for page in doc:
            offsets.append(total_chars)
            page_text = page.get_text("text")
            pages.append(page_text)
            total_chars += len(page_text)

        full_text = "".join(pages)

        avg_chars_per_page = total_chars / max(doc.page_count, 1)
        if avg_chars_per_page < MIN_TEXT_CHARS_PER_PAGE:
            raise PdfExtractionError(
                f"PDF has no text layer (avg {avg_chars_per_page:.0f} chars/page). "
                "Scanned PDFs are not supported in MVP."
            )

        return PdfExtractionResult(
            text=full_text,
            page_count=doc.page_count,
            page_offsets=offsets,
            extraction_tool="pymupdf",
            extraction_version=fitz.VersionBind,
        )
    finally:
        doc.close()
```

- [ ] **Step 7.5: Create package markers**

```bash
touch app/ingest/extractors/__init__.py tests/ingest/extractors/__init__.py
```

- [ ] **Step 7.6: Run test — expect PASS**

Run: `uv run pytest tests/ingest/extractors/test_pdf.py -v`
Expected: `2 passed`

- [ ] **Step 7.7: Commit**

```bash
git add app/ingest/extractors/ tests/ingest/extractors/ tests/fixtures/sample.pdf tests/fixtures/scanned.pdf
git commit -m "feat(ingest): pdf extraction via pymupdf with scanned-pdf rejection"
```

---

## Task 8: DOCX Extractor

**Files:**
- Create: `app/ingest/extractors/docx.py`
- Create: `tests/ingest/extractors/test_docx.py`
- Create: `tests/fixtures/sample.docx`

- [ ] **Step 8.1: Generate test DOCX fixture**

```bash
uv run python -c '
from docx import Document
doc = Document()
doc.add_heading("Master Services Agreement", level=0)
doc.add_heading("1. Definitions", level=1)
doc.add_paragraph("\"Services\" means the cloud-based software offering.")
doc.add_heading("2. Payment Terms", level=1)
doc.add_paragraph("Customer shall pay all undisputed invoices within thirty (30) days.")
doc.save("tests/fixtures/sample.docx")
'
```

- [ ] **Step 8.2: Write failing test `tests/ingest/extractors/test_docx.py`**

```python
from pathlib import Path
from app.ingest.extractors.docx import extract_docx


FIXTURES = Path(__file__).parent.parent.parent / "fixtures"


def test_extract_docx_returns_structured_blocks():
    result = extract_docx(FIXTURES / "sample.docx")
    headings = [b for b in result.blocks if b.style.startswith("Heading")]
    paragraphs = [b for b in result.blocks if b.style == "Normal"]

    assert any("Definitions" in b.text for b in headings)
    assert any("Payment Terms" in b.text for b in headings)
    assert any("undisputed invoices" in b.text for b in paragraphs)
    assert result.extraction_tool == "python-docx"
```

- [ ] **Step 8.3: Run test — expect FAIL**

Run: `uv run pytest tests/ingest/extractors/test_docx.py -v`
Expected: import error.

- [ ] **Step 8.4: Implement `app/ingest/extractors/docx.py`**

```python
from dataclasses import dataclass
from pathlib import Path
import docx


@dataclass(frozen=True)
class DocxBlock:
    text: str
    style: str
    level: int | None  # heading level if applicable


@dataclass(frozen=True)
class DocxExtractionResult:
    blocks: list[DocxBlock]
    extraction_tool: str
    extraction_version: str


def extract_docx(path: Path) -> DocxExtractionResult:
    doc = docx.Document(str(path))
    blocks: list[DocxBlock] = []

    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        style_name = p.style.name if p.style else "Normal"
        level = None
        if style_name.startswith("Heading "):
            try:
                level = int(style_name.split()[1])
            except (IndexError, ValueError):
                level = None
        blocks.append(DocxBlock(text=text, style=style_name, level=level))

    return DocxExtractionResult(
        blocks=blocks,
        extraction_tool="python-docx",
        extraction_version=docx.__version__,
    )
```

- [ ] **Step 8.5: Run test — expect PASS**

Run: `uv run pytest tests/ingest/extractors/test_docx.py -v`
Expected: `1 passed`

- [ ] **Step 8.6: Commit**

```bash
git add app/ingest/extractors/docx.py tests/ingest/extractors/test_docx.py tests/fixtures/sample.docx
git commit -m "feat(ingest): docx extraction preserving heading structure"
```

---

## Task 9: Clause Segmenter

**Files:**
- Create: `app/ingest/segmenter.py`
- Create: `tests/ingest/test_segmenter.py`

This module takes a unified representation (list of text blocks with optional heading info) and produces `Clause` records with `section_path`, `heading_text`, `text_display`, and character offsets.

- [ ] **Step 9.1: Write failing test `tests/ingest/test_segmenter.py`**

```python
from app.ingest.segmenter import segment_clauses, SegmenterBlock


def test_segmenter_groups_paragraphs_under_headings():
    blocks = [
        SegmenterBlock(text="Master Services Agreement", kind="heading", level=0),
        SegmenterBlock(text="1. Definitions", kind="heading", level=1),
        SegmenterBlock(text="\"Services\" means the cloud offering.", kind="paragraph"),
        SegmenterBlock(text="2. Payment Terms", kind="heading", level=1),
        SegmenterBlock(text="Customer shall pay invoices within 30 days.", kind="paragraph"),
        SegmenterBlock(text="Late payments accrue 1.5% monthly interest.", kind="paragraph"),
    ]

    clauses = segment_clauses(blocks)
    assert len(clauses) == 3
    assert clauses[0].heading_text == "1. Definitions"
    assert "cloud offering" in clauses[0].text_display
    assert clauses[1].heading_text == "2. Payment Terms"
    assert "30 days" in clauses[1].text_display
    assert "1.5% monthly" in clauses[2].text_display
    assert clauses[2].heading_text == "2. Payment Terms"  # same section, sub-clause


def test_segmenter_handles_no_headings():
    blocks = [SegmenterBlock(text="Some free text.", kind="paragraph")]
    clauses = segment_clauses(blocks)
    assert len(clauses) == 1
    assert clauses[0].heading_text is None


def test_segmenter_splits_payment_subclauses():
    blocks = [
        SegmenterBlock(text="4. Payment", kind="heading", level=1),
        SegmenterBlock(text="(a) Invoicing. Provider shall invoice monthly.", kind="paragraph"),
        SegmenterBlock(text="(b) Due Date. Payments are due within 30 days.", kind="paragraph"),
        SegmenterBlock(text="(c) Late Fees. Interest at 1.5% per month.", kind="paragraph"),
    ]
    clauses = segment_clauses(blocks)
    assert len(clauses) == 3  # each subclause is its own clause
```

- [ ] **Step 9.2: Run test — expect FAIL**

Run: `uv run pytest tests/ingest/test_segmenter.py -v`
Expected: import error.

- [ ] **Step 9.3: Implement `app/ingest/segmenter.py`**

```python
import re
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class SegmenterBlock:
    text: str
    kind: Literal["heading", "paragraph"]
    level: int | None = None


@dataclass(frozen=True)
class SegmentedClause:
    heading_text: str | None
    section_path: str | None
    text_display: str
    char_start: int
    char_end: int


# matches "(a)", "(i)", "1.", "1.1", "1.1.1"
SUBCLAUSE_MARKER = re.compile(r"^\s*(\([a-zA-Z0-9]+\)|\d+(\.\d+)*\.)\s+")


def segment_clauses(blocks: list[SegmenterBlock]) -> list[SegmentedClause]:
    clauses: list[SegmentedClause] = []
    heading_stack: list[str] = []
    current_heading: str | None = None
    char_cursor = 0

    for block in blocks:
        if block.kind == "heading":
            if block.level is not None and block.level > 0:
                while len(heading_stack) >= block.level:
                    heading_stack.pop()
                heading_stack.append(block.text)
                current_heading = block.text
            else:
                current_heading = block.text
            char_cursor += len(block.text) + 1
            continue

        is_subclause = bool(SUBCLAUSE_MARKER.match(block.text))
        section_path = " › ".join(heading_stack) if heading_stack else None

        text = block.text.strip()
        start = char_cursor
        end = char_cursor + len(text)
        char_cursor = end + 1

        if is_subclause or not clauses or clauses[-1].heading_text != current_heading:
            clauses.append(
                SegmentedClause(
                    heading_text=current_heading,
                    section_path=section_path,
                    text_display=text,
                    char_start=start,
                    char_end=end,
                )
            )
        else:
            prev = clauses[-1]
            clauses[-1] = SegmentedClause(
                heading_text=prev.heading_text,
                section_path=prev.section_path,
                text_display=prev.text_display + "\n" + text,
                char_start=prev.char_start,
                char_end=end,
            )

    return clauses
```

- [ ] **Step 9.4: Run test — expect PASS**

Run: `uv run pytest tests/ingest/test_segmenter.py -v`
Expected: `3 passed`

- [ ] **Step 9.5: Commit**

```bash
git add app/ingest/segmenter.py tests/ingest/test_segmenter.py
git commit -m "feat(ingest): structure-aware clause segmenter with subclause detection"
```

---

## Task 10: Metadata Extractor

**Files:**
- Create: `app/ingest/metadata.py`
- Create: `tests/ingest/test_metadata.py`

Extracts agreement_type, executed_status, governing_law, client/counterparty names. MVP uses simple pattern matching with confidence levels; no LLM needed for these (LLM is reserved for clause-family classification).

- [ ] **Step 10.1: Write failing test `tests/ingest/test_metadata.py`**

```python
from app.ingest.metadata import extract_contract_metadata


def test_extracts_governing_law_explicit():
    text = "This Agreement is governed by the laws of the State of New York."
    md = extract_contract_metadata(text)
    assert md.governing_law == "New York"
    assert md.governing_law_confidence == "high"


def test_detects_saas_msa_title():
    text = "MASTER SERVICES AGREEMENT\n\nThis SaaS Master Services Agreement..."
    md = extract_contract_metadata(text)
    assert md.agreement_type == "SaaS_MSA"
    assert md.agreement_type_confidence in ("high", "medium")


def test_executed_status_from_signature_block():
    text = "IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above."
    md = extract_contract_metadata(text)
    assert md.executed_status == "executed"


def test_missing_governing_law_returns_null_low_conf():
    md = extract_contract_metadata("just some generic contract language")
    assert md.governing_law is None
    assert md.governing_law_confidence == "low"
```

- [ ] **Step 10.2: Run test — expect FAIL**

Run: `uv run pytest tests/ingest/test_metadata.py -v`
Expected: import error.

- [ ] **Step 10.3: Implement `app/ingest/metadata.py`**

```python
import re
from dataclasses import dataclass
from typing import Literal

Confidence = Literal["high", "medium", "low"]


@dataclass(frozen=True)
class ContractMetadata:
    agreement_type: str | None
    agreement_type_confidence: Confidence
    executed_status: str | None
    executed_status_confidence: Confidence
    governing_law: str | None
    governing_law_confidence: Confidence


US_STATES = [
    "New York", "California", "Delaware", "Texas", "Massachusetts", "Illinois",
    "Washington", "Florida", "Pennsylvania", "Virginia", "Georgia", "Colorado",
]


GOVERNING_LAW_PATTERNS = [
    re.compile(
        r"governed\s+by\s+(?:and\s+construed\s+in\s+accordance\s+with\s+)?"
        r"the\s+laws?\s+of\s+(?:the\s+State\s+of\s+)?([A-Z][A-Za-z ]+?)(?:[,.\s]|$)",
        re.IGNORECASE,
    ),
    re.compile(r"State\s+of\s+([A-Z][A-Za-z ]+?)\s+law", re.IGNORECASE),
]


def extract_contract_metadata(text: str) -> ContractMetadata:
    agreement_type, at_conf = _detect_agreement_type(text)
    executed, ex_conf = _detect_executed(text)
    gov_law, gl_conf = _detect_governing_law(text)

    return ContractMetadata(
        agreement_type=agreement_type,
        agreement_type_confidence=at_conf,
        executed_status=executed,
        executed_status_confidence=ex_conf,
        governing_law=gov_law,
        governing_law_confidence=gl_conf,
    )


def _detect_agreement_type(text: str) -> tuple[str | None, Confidence]:
    head = text[:2000]
    if re.search(r"master\s+services?\s+agreement", head, re.IGNORECASE):
        if re.search(r"saas|software[- ]as[- ]a[- ]service|subscription", head, re.IGNORECASE):
            return "SaaS_MSA", "high"
        return "SaaS_MSA", "medium"
    return None, "low"


def _detect_executed(text: str) -> tuple[str | None, Confidence]:
    if re.search(r"in\s+witness\s+whereof", text, re.IGNORECASE):
        return "executed", "high"
    if re.search(r"executed\s+(?:this|as\s+of)", text, re.IGNORECASE):
        return "executed", "high"
    return None, "low"


def _detect_governing_law(text: str) -> tuple[str | None, Confidence]:
    for pat in GOVERNING_LAW_PATTERNS:
        m = pat.search(text)
        if m:
            candidate = m.group(1).strip().rstrip(",.")
            for st in US_STATES:
                if candidate.lower() == st.lower():
                    return st, "high"
            if candidate and len(candidate) < 40:
                return candidate, "medium"
    return None, "low"
```

- [ ] **Step 10.4: Run test — expect PASS**

Run: `uv run pytest tests/ingest/test_metadata.py -v`
Expected: `4 passed`

- [ ] **Step 10.5: Commit**

```bash
git add app/ingest/metadata.py tests/ingest/test_metadata.py
git commit -m "feat(ingest): pattern-based contract metadata extraction with confidence"
```

---

## Task 11: Clause-Family Taxonomy & Classifier

**Files:**
- Create: `app/ingest/taxonomy.py`
- Create: `app/ingest/classifier.py`
- Create: `tests/ingest/test_classifier.py`

- [ ] **Step 11.1: Write failing test `tests/ingest/test_classifier.py`**

```python
from unittest.mock import MagicMock, patch
from app.ingest.classifier import classify_clause, ClauseClassification
from app.ingest.taxonomy import ClauseFamily


@patch("app.ingest.classifier.OpenAI")
def test_classifier_parses_structured_output(MockOpenAI):
    client = MagicMock()
    MockOpenAI.return_value = client
    client.chat.completions.parse.return_value.choices = [
        MagicMock(message=MagicMock(parsed=ClauseClassification(
            family=ClauseFamily.PAYMENT_TERMS,
            confidence="high",
            rationale="Clause about net 30 payment.",
        )))
    ]

    result = classify_clause(
        heading_text="Payment Terms",
        section_path="Article 4",
        clause_text="Customer shall pay invoices within 30 days.",
    )
    assert result.family == ClauseFamily.PAYMENT_TERMS
    assert result.confidence == "high"


@patch("app.ingest.classifier.OpenAI")
def test_classifier_handles_null_family(MockOpenAI):
    client = MagicMock()
    MockOpenAI.return_value = client
    client.chat.completions.parse.return_value.choices = [
        MagicMock(message=MagicMock(parsed=ClauseClassification(
            family=None,
            confidence="low",
            rationale="No clear family match.",
        )))
    ]

    result = classify_clause(heading_text=None, section_path=None, clause_text="xyz")
    assert result.family is None
    assert result.confidence == "low"
```

- [ ] **Step 11.2: Run test — expect FAIL**

Run: `uv run pytest tests/ingest/test_classifier.py -v`
Expected: import error.

- [ ] **Step 11.3: Implement `app/ingest/taxonomy.py`**

```python
from enum import StrEnum


class ClauseFamily(StrEnum):
    DEFINITIONS = "definitions"
    FEES_AND_PRICING = "fees_and_pricing"
    PAYMENT_TERMS = "payment_terms"
    LATE_PAYMENT_AND_SUSPENSION = "late_payment_and_suspension"
    TERM_AND_RENEWAL = "term_and_renewal"
    TERMINATION = "termination"
    SERVICE_LEVELS = "service_levels"
    SUPPORT_AND_MAINTENANCE = "support_and_maintenance"
    DATA_SECURITY = "data_security"
    DATA_PRIVACY = "data_privacy"
    CONFIDENTIALITY = "confidentiality"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    WARRANTIES_AND_DISCLAIMERS = "warranties_and_disclaimers"
    LIMITATION_OF_LIABILITY = "limitation_of_liability"
    INDEMNIFICATION = "indemnification"
    INSURANCE = "insurance"
    GOVERNING_LAW_AND_JURISDICTION = "governing_law_and_jurisdiction"
    DISPUTE_RESOLUTION = "dispute_resolution"
    ASSIGNMENT_AND_CHANGE_OF_CONTROL = "assignment_and_change_of_control"
    GENERAL_BOILERPLATE = "general_boilerplate"


CLASSIFIER_SYSTEM_PROMPT = """You classify clauses from executed SaaS Master Services \
Agreements into one of 20 families. If no family clearly fits, return family=null with \
confidence=low. Never invent new family names."""


def build_classifier_user_prompt(
    heading_text: str | None,
    section_path: str | None,
    clause_text: str,
) -> str:
    return (
        f'HEADING: "{heading_text or ""}"\n'
        f'SECTION PATH: "{section_path or ""}"\n'
        f"CLAUSE TEXT:\n{clause_text}"
    )
```

- [ ] **Step 11.4: Implement `app/ingest/classifier.py`**

```python
from typing import Literal
from pydantic import BaseModel
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import get_settings
from app.ingest.taxonomy import (
    ClauseFamily,
    CLASSIFIER_SYSTEM_PROMPT,
    build_classifier_user_prompt,
)


class ClauseClassification(BaseModel):
    family: ClauseFamily | None
    confidence: Literal["high", "medium", "low"]
    rationale: str


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def classify_clause(
    heading_text: str | None,
    section_path: str | None,
    clause_text: str,
) -> ClauseClassification:
    s = get_settings()
    client = OpenAI(api_key=s.openai_api_key)

    response = client.chat.completions.parse(
        model=s.openai_classifier_model,
        messages=[
            {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
            {"role": "user", "content": build_classifier_user_prompt(
                heading_text, section_path, clause_text
            )},
        ],
        response_format=ClauseClassification,
    )
    return response.choices[0].message.parsed
```

- [ ] **Step 11.5: Run test — expect PASS**

Run: `uv run pytest tests/ingest/test_classifier.py -v`
Expected: `2 passed`

- [ ] **Step 11.6: Commit**

```bash
git add app/ingest/taxonomy.py app/ingest/classifier.py tests/ingest/test_classifier.py
git commit -m "feat(ingest): 20-family taxonomy + gpt-5-mini structured classifier"
```

---

## Task 12: Embedder

**Files:**
- Create: `app/ingest/embedder.py`
- Create: `tests/ingest/test_embedder.py`

- [ ] **Step 12.1: Write failing test `tests/ingest/test_embedder.py`**

```python
from unittest.mock import MagicMock, patch
from app.ingest.embedder import embed_texts


@patch("app.ingest.embedder.OpenAI")
def test_embed_texts_returns_one_vector_per_input(MockOpenAI):
    client = MagicMock()
    MockOpenAI.return_value = client
    client.embeddings.create.return_value.data = [
        MagicMock(embedding=[0.1] * 3072),
        MagicMock(embedding=[0.2] * 3072),
    ]

    vecs = embed_texts(["first clause", "second clause"])
    assert len(vecs) == 2
    assert len(vecs[0]) == 3072
    assert vecs[0][0] == 0.1


@patch("app.ingest.embedder.OpenAI")
def test_embed_texts_batches_over_max_inputs(MockOpenAI):
    client = MagicMock()
    MockOpenAI.return_value = client
    client.embeddings.create.return_value.data = [MagicMock(embedding=[0.0] * 3072)] * 128

    # 300 inputs should trigger 3 API calls (batch size 128)
    vecs = embed_texts(["x"] * 300)
    assert client.embeddings.create.call_count == 3
    assert len(vecs) == 300
```

- [ ] **Step 12.2: Run test — expect FAIL**

Run: `uv run pytest tests/ingest/test_embedder.py -v`
Expected: import error.

- [ ] **Step 12.3: Implement `app/ingest/embedder.py`**

```python
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import get_settings


MAX_BATCH = 128


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _embed_batch(client: OpenAI, texts: list[str], model: str) -> list[list[float]]:
    response = client.embeddings.create(model=model, input=texts)
    return [d.embedding for d in response.data]


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    s = get_settings()
    client = OpenAI(api_key=s.openai_api_key)

    out: list[list[float]] = []
    for i in range(0, len(texts), MAX_BATCH):
        batch = texts[i : i + MAX_BATCH]
        out.extend(_embed_batch(client, batch, s.openai_embedding_model))
    return out
```

- [ ] **Step 12.4: Run test — expect PASS**

Run: `uv run pytest tests/ingest/test_embedder.py -v`
Expected: `2 passed`

- [ ] **Step 12.5: Commit**

```bash
git add app/ingest/embedder.py tests/ingest/test_embedder.py
git commit -m "feat(ingest): batched openai embeddings with retry"
```

---

## Task 13: Persistence Layer

**Files:**
- Create: `app/ingest/persistence.py`
- Create: `tests/ingest/test_persistence.py`

Writes a `Contract` + its `Clause` records to Postgres, then indexes clauses into OpenSearch. Idempotent on `checksum_sha256`.

- [ ] **Step 13.1: Write failing test `tests/ingest/test_persistence.py`**

```python
from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.models import Base, Contract
from app.ingest.persistence import persist_ingest, IngestPayload, ClausePayload


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_persist_writes_contract_and_clauses(session):
    os_client = MagicMock()
    payload = IngestPayload(
        contract_id="ctr_test",
        title="Test MSA",
        agreement_type="SaaS_MSA",
        executed_status="executed",
        governing_law="New York",
        client_name=None,
        counterparty_name=None,
        source_file_path="/tmp/x.pdf",
        source_filename="x.pdf",
        checksum_sha256="aaa",
        extraction_tool="pymupdf",
        extraction_version="1.24",
        clauses=[
            ClausePayload(
                clause_id="cl_1",
                section_path="Article 4",
                heading_text="Payment",
                clause_family="payment_terms",
                text_display="Customer shall pay...",
                text_normalized="customer shall pay",
                char_start=0,
                char_end=20,
                embedding=[0.0] * 3072,
            )
        ],
    )

    persist_ingest(session, os_client, payload)

    contract = session.get(Contract, "ctr_test")
    assert contract is not None
    assert contract.ingest_status == "indexed"
    assert os_client.index.called


def test_persist_rejects_duplicate_checksum(session):
    from app.db.models import Contract as ContractModel
    existing = ContractModel(
        contract_id="ctr_existing",
        title="Old",
        agreement_type="SaaS_MSA",
        executed_status="executed",
        source_filename="old.pdf",
        source_file_path="/tmp/old.pdf",
        checksum_sha256="same_hash",
        extraction_tool="pymupdf",
        extraction_version="1.24",
        ingest_status="indexed",
        created_at=datetime.now(timezone.utc),
    )
    session.add(existing)
    session.commit()

    os_client = MagicMock()
    payload = IngestPayload(
        contract_id="ctr_dup",
        title="Dup",
        agreement_type="SaaS_MSA",
        executed_status="executed",
        governing_law=None,
        client_name=None,
        counterparty_name=None,
        source_file_path="/tmp/dup.pdf",
        source_filename="dup.pdf",
        checksum_sha256="same_hash",
        extraction_tool="pymupdf",
        extraction_version="1.24",
        clauses=[],
    )

    with pytest.raises(ValueError, match="already ingested"):
        persist_ingest(session, os_client, payload)
```

- [ ] **Step 13.2: Run test — expect FAIL**

Run: `uv run pytest tests/ingest/test_persistence.py -v`
Expected: import error.

- [ ] **Step 13.3: Implement `app/ingest/persistence.py`**

```python
from dataclasses import dataclass
from datetime import datetime, timezone
from opensearchpy import OpenSearch
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import get_settings
from app.db.models import Contract, Clause, MetadataConfidence


@dataclass(frozen=True)
class ClausePayload:
    clause_id: str
    section_path: str | None
    heading_text: str | None
    clause_family: str | None
    text_display: str
    text_normalized: str
    char_start: int
    char_end: int
    embedding: list[float]


@dataclass(frozen=True)
class IngestPayload:
    contract_id: str
    title: str
    agreement_type: str
    executed_status: str
    governing_law: str | None
    client_name: str | None
    counterparty_name: str | None
    source_file_path: str
    source_filename: str
    checksum_sha256: str
    extraction_tool: str
    extraction_version: str
    clauses: list[ClausePayload]


def persist_ingest(
    session: Session,
    os_client: OpenSearch,
    payload: IngestPayload,
) -> None:
    s = get_settings()

    existing = session.execute(
        select(Contract).where(Contract.checksum_sha256 == payload.checksum_sha256)
    ).scalar_one_or_none()
    if existing is not None:
        raise ValueError(f"Contract already ingested (checksum {payload.checksum_sha256})")

    now = datetime.now(timezone.utc)
    contract = Contract(
        contract_id=payload.contract_id,
        title=payload.title,
        agreement_type=payload.agreement_type,
        executed_status=payload.executed_status,
        governing_law=payload.governing_law,
        client_name=payload.client_name,
        counterparty_name=payload.counterparty_name,
        source_file_path=payload.source_file_path,
        source_filename=payload.source_filename,
        checksum_sha256=payload.checksum_sha256,
        extraction_tool=payload.extraction_tool,
        extraction_version=payload.extraction_version,
        ingest_status="parsed",
        created_at=now,
    )
    session.add(contract)
    session.flush()

    for cp in payload.clauses:
        clause = Clause(
            clause_id=cp.clause_id,
            contract_id=payload.contract_id,
            section_path=cp.section_path,
            heading_text=cp.heading_text,
            clause_family=cp.clause_family,
            text_display=cp.text_display,
            text_normalized=cp.text_normalized,
            char_start=cp.char_start,
            char_end=cp.char_end,
            embedding=cp.embedding,
            embedding_model=s.openai_embedding_model,
            embedding_version=now.strftime("%Y-%m"),
            embedding_created_at=now,
            language="en",
            jurisdiction=None,
            created_at=now,
        )
        session.add(clause)

    session.flush()

    for cp in payload.clauses:
        os_client.index(
            index=s.opensearch_clauses_index,
            id=cp.clause_id,
            body={
                "clause_id": cp.clause_id,
                "contract_id": payload.contract_id,
                "agreement_type": payload.agreement_type,
                "clause_family": cp.clause_family,
                "governing_law": payload.governing_law,
                "section_path": cp.section_path,
                "heading_text": cp.heading_text,
                "text_display": cp.text_display,
                "text_normalized": cp.text_normalized,
                "embedding": cp.embedding,
            },
        )

    contract.ingest_status = "indexed"
    session.commit()
```

- [ ] **Step 13.4: Run test — expect PASS**

Run: `uv run pytest tests/ingest/test_persistence.py -v`
Expected: `2 passed`

- [ ] **Step 13.5: Commit**

```bash
git add app/ingest/persistence.py tests/ingest/test_persistence.py
git commit -m "feat(ingest): persistence to postgres + opensearch with dedup"
```

---

## Task 14: Ingestion Orchestrator

**Files:**
- Create: `app/ingest/orchestrator.py`
- Create: `tests/ingest/test_orchestrator.py`

Wires tasks 6–13 together.

- [ ] **Step 14.1: Write failing test `tests/ingest/test_orchestrator.py`**

```python
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.models import Base, Contract
from app.ingest.orchestrator import ingest_contract


FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@patch("app.ingest.orchestrator.classify_clause")
@patch("app.ingest.orchestrator.embed_texts")
def test_ingest_pdf_end_to_end(mock_embed, mock_classify, session):
    from app.ingest.classifier import ClauseClassification
    from app.ingest.taxonomy import ClauseFamily

    mock_embed.return_value = [[0.0] * 3072, [0.0] * 3072]
    mock_classify.return_value = ClauseClassification(
        family=ClauseFamily.PAYMENT_TERMS,
        confidence="high",
        rationale="ok",
    )
    os_client = MagicMock()

    contract_id = ingest_contract(
        session=session,
        os_client=os_client,
        file_path=FIXTURES / "sample.pdf",
    )

    assert contract_id is not None
    contract = session.get(Contract, contract_id)
    assert contract is not None
    assert contract.ingest_status == "indexed"
    assert len(contract.clauses) >= 1
```

- [ ] **Step 14.2: Run test — expect FAIL**

Run: `uv run pytest tests/ingest/test_orchestrator.py -v`
Expected: import error.

- [ ] **Step 14.3: Implement `app/ingest/orchestrator.py`**

```python
import re
import uuid
from pathlib import Path
from opensearchpy import OpenSearch
from sqlalchemy.orm import Session
from app.ingest.intake import intake_file
from app.ingest.extractors.pdf import extract_pdf
from app.ingest.extractors.docx import extract_docx
from app.ingest.segmenter import segment_clauses, SegmenterBlock
from app.ingest.metadata import extract_contract_metadata
from app.ingest.classifier import classify_clause
from app.ingest.embedder import embed_texts
from app.ingest.persistence import persist_ingest, IngestPayload, ClausePayload


def _blocks_from_pdf(path: Path) -> tuple[list[SegmenterBlock], str, str, str]:
    result = extract_pdf(path)
    blocks: list[SegmenterBlock] = []
    for line in result.text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^\d+\.\s+[A-Z]", stripped):
            blocks.append(SegmenterBlock(text=stripped, kind="heading", level=1))
        else:
            blocks.append(SegmenterBlock(text=stripped, kind="paragraph"))
    return blocks, result.text, result.extraction_tool, result.extraction_version


def _blocks_from_docx(path: Path) -> tuple[list[SegmenterBlock], str, str, str]:
    result = extract_docx(path)
    blocks: list[SegmenterBlock] = []
    joined_text_parts: list[str] = []
    for b in result.blocks:
        kind = "heading" if b.style.startswith("Heading") else "paragraph"
        blocks.append(SegmenterBlock(text=b.text, kind=kind, level=b.level))
        joined_text_parts.append(b.text)
    return blocks, "\n".join(joined_text_parts), result.extraction_tool, result.extraction_version


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def ingest_contract(
    session: Session,
    os_client: OpenSearch,
    file_path: Path,
) -> str:
    intake = intake_file(file_path)

    if intake.file_extension == ".pdf":
        blocks, full_text, tool, version = _blocks_from_pdf(file_path)
    elif intake.file_extension == ".docx":
        blocks, full_text, tool, version = _blocks_from_docx(file_path)
    else:
        raise ValueError(f"Unreachable: {intake.file_extension}")

    md = extract_contract_metadata(full_text)
    segments = segment_clauses(blocks)

    clause_texts = [seg.text_display for seg in segments]
    embeddings = embed_texts(clause_texts) if clause_texts else []

    classifications = [
        classify_clause(
            heading_text=seg.heading_text,
            section_path=seg.section_path,
            clause_text=seg.text_display,
        )
        for seg in segments
    ]

    contract_id = f"ctr_{uuid.uuid4().hex[:12]}"

    clause_payloads: list[ClausePayload] = []
    for seg, cls, emb in zip(segments, classifications, embeddings, strict=True):
        clause_payloads.append(
            ClausePayload(
                clause_id=f"cl_{uuid.uuid4().hex[:12]}",
                section_path=seg.section_path,
                heading_text=seg.heading_text,
                clause_family=cls.family.value if cls.family else None,
                text_display=seg.text_display,
                text_normalized=_normalize_text(seg.text_display),
                char_start=seg.char_start,
                char_end=seg.char_end,
                embedding=emb,
            )
        )

    payload = IngestPayload(
        contract_id=contract_id,
        title=intake.source_filename.rsplit(".", 1)[0],
        agreement_type=md.agreement_type or "SaaS_MSA",
        executed_status=md.executed_status or "unknown",
        governing_law=md.governing_law,
        client_name=None,
        counterparty_name=None,
        source_file_path=intake.source_file_path,
        source_filename=intake.source_filename,
        checksum_sha256=intake.checksum_sha256,
        extraction_tool=tool,
        extraction_version=version,
        clauses=clause_payloads,
    )

    persist_ingest(session, os_client, payload)
    return contract_id
```

- [ ] **Step 14.4: Run test — expect PASS**

Run: `uv run pytest tests/ingest/test_orchestrator.py -v`
Expected: `1 passed`

- [ ] **Step 14.5: Commit**

```bash
git add app/ingest/orchestrator.py tests/ingest/test_orchestrator.py
git commit -m "feat(ingest): orchestrator wiring intake→extract→segment→classify→embed→persist"
```

---

## Task 15: CLI

**Files:**
- Create: `app/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 15.1: Write failing test `tests/test_cli.py`**

```python
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from app.cli import cli


@patch("app.cli.ingest_contract")
@patch("app.cli.make_client")
@patch("app.cli.make_session_factory")
def test_cli_ingest_file(mock_factory, mock_os, mock_ingest, tmp_path):
    mock_factory.return_value = MagicMock()
    mock_os.return_value = MagicMock()
    mock_ingest.return_value = "ctr_abc"

    f = tmp_path / "x.pdf"
    f.write_bytes(b"pdf")

    runner = CliRunner()
    result = runner.invoke(cli, ["ingest", str(f)])
    assert result.exit_code == 0
    assert "ctr_abc" in result.output
    mock_ingest.assert_called_once()
```

- [ ] **Step 15.2: Run test — expect FAIL**

Run: `uv run pytest tests/test_cli.py -v`
Expected: import error.

- [ ] **Step 15.3: Implement `app/cli.py`**

```python
from pathlib import Path
import click
from app.db.session import make_session_factory
from app.search.client import make_client
from app.search.index_mapping import ensure_clauses_index
from app.ingest.orchestrator import ingest_contract


@click.group()
def cli() -> None:
    """ClauseIQ CLI."""


@cli.command("init-index")
def init_index_cmd() -> None:
    """Ensure the OpenSearch clauses index exists."""
    client = make_client()
    ensure_clauses_index(client)
    click.echo("ok")


@cli.command("ingest")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
def ingest_cmd(path: Path) -> None:
    """Ingest a single contract file."""
    factory = make_session_factory()
    os_client = make_client()

    files = [path] if path.is_file() else list(path.glob("*.pdf")) + list(path.glob("*.docx"))

    with factory() as session:
        for f in files:
            try:
                cid = ingest_contract(session, os_client, f)
                click.echo(f"ingested {f.name} -> {cid}")
            except ValueError as e:
                click.echo(f"skip {f.name}: {e}", err=True)


if __name__ == "__main__":
    cli()
```

- [ ] **Step 15.4: Run test — expect PASS**

Run: `uv run pytest tests/test_cli.py -v`
Expected: `1 passed`

- [ ] **Step 15.5: Commit**

```bash
git add app/cli.py tests/test_cli.py
git commit -m "feat(cli): click-based cli with ingest and init-index commands"
```

---

## Task 16: End-to-End Integration Test

**Files:**
- Create: `tests/integration/__init__.py`
- Create: `tests/integration/test_ingest_e2e.py`
- Create: `tests/conftest.py`

This test runs the full pipeline against a live Postgres + OpenSearch (via testcontainers), but **mocks the OpenAI calls** — we don't want CI to depend on OpenAI credits.

- [ ] **Step 16.1: Create `tests/conftest.py`**

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from testcontainers.postgres import PostgresContainer
from testcontainers.opensearch import OpenSearchContainer
from app.db.models import Base


@pytest.fixture(scope="session")
def pg_url():
    with PostgresContainer("postgres:16") as pg:
        yield pg.get_connection_url().replace("postgresql+psycopg2", "postgresql+psycopg")


@pytest.fixture(scope="session")
def os_container():
    with OpenSearchContainer("opensearchproject/opensearch:2.15.0") as os_c:
        yield os_c


@pytest.fixture()
def db_session(pg_url):
    engine = create_engine(pg_url)
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)
```

- [ ] **Step 16.2: Write E2E test `tests/integration/test_ingest_e2e.py`**

```python
from pathlib import Path
from unittest.mock import patch
import pytest
from opensearchpy import OpenSearch
from app.ingest.orchestrator import ingest_contract
from app.ingest.classifier import ClauseClassification
from app.ingest.taxonomy import ClauseFamily
from app.search.index_mapping import ensure_clauses_index


FIXTURES = Path(__file__).parent.parent / "fixtures"


@patch("app.ingest.orchestrator.classify_clause")
@patch("app.ingest.orchestrator.embed_texts")
def test_full_pipeline_pdf(mock_embed, mock_classify, db_session, os_container):
    mock_classify.return_value = ClauseClassification(
        family=ClauseFamily.PAYMENT_TERMS, confidence="high", rationale="test"
    )

    client = OpenSearch(
        hosts=[os_container.get_config()["host"]],
        http_auth=("admin", "admin"),
        use_ssl=False,
    )
    ensure_clauses_index(client)

    # embeddings for 2 expected clauses
    mock_embed.return_value = [[0.0] * 3072] * 10

    cid = ingest_contract(db_session, client, FIXTURES / "sample.pdf")

    assert cid is not None
    # assert OpenSearch has the clauses indexed
    client.indices.refresh(index="clauses")
    resp = client.search(index="clauses", body={"query": {"term": {"contract_id": cid}}})
    assert resp["hits"]["total"]["value"] >= 1
```

- [ ] **Step 16.3: Run E2E test — expect PASS**

Run: `uv run pytest tests/integration/test_ingest_e2e.py -v`
Expected: `1 passed` (may take ~30s on first run while containers download).

- [ ] **Step 16.4: Commit**

```bash
git add tests/integration/ tests/conftest.py
git commit -m "test(integration): end-to-end pipeline test with live postgres + opensearch"
```

---

## Task 17: Manual Smoke Test Against Seed Corpus

**Files:** (no new code; this is a manual verification task)

- [ ] **Step 17.1: Place 3 real SaaS MSA PDFs/DOCX in `contracts/source_files/`**

Run:
```bash
mkdir -p contracts/source_files
# Manually copy 3 contracts into contracts/source_files/
ls contracts/source_files/
```

Expected: 3 files listed.

- [ ] **Step 17.2: Start services and apply migrations**

```bash
docker compose up -d
uv run alembic upgrade head
uv run clauseiq init-index
```

Expected: Postgres and OpenSearch up, schema applied, index created.

- [ ] **Step 17.3: Set `OPENAI_API_KEY` in `.env`**

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
```

- [ ] **Step 17.4: Ingest the 3 contracts**

```bash
uv run clauseiq ingest contracts/source_files/
```

Expected: 3 lines `ingested <filename> -> ctr_xxx`.

- [ ] **Step 17.5: Verify Postgres**

```bash
docker compose exec postgres psql -U clauseiq -d clauseiq -c "SELECT contract_id, title, ingest_status FROM contracts;"
docker compose exec postgres psql -U clauseiq -d clauseiq -c "SELECT clause_family, COUNT(*) FROM clauses GROUP BY clause_family ORDER BY COUNT(*) DESC;"
```

Expected: 3 contracts with `ingest_status=indexed`. Family distribution should reasonably span the taxonomy (no single family >50%).

- [ ] **Step 17.6: Verify OpenSearch**

```bash
curl -s "http://localhost:9200/clauses/_count" | python -m json.tool
curl -s -XGET "http://localhost:9200/clauses/_search?size=1" | python -m json.tool
```

Expected: count matches total clauses in Postgres; a sample document shows all expected fields.

- [ ] **Step 17.7: Taxonomy validation**

Run:
```bash
docker compose exec postgres psql -U clauseiq -d clauseiq -c "
SELECT clause_family, COUNT(*)
FROM clauses
GROUP BY clause_family
ORDER BY COUNT(*) DESC;
"
```

Manually eyeball 30 random clauses:
```bash
docker compose exec postgres psql -U clauseiq -d clauseiq -c "
SELECT clause_family, LEFT(text_display, 200)
FROM clauses
ORDER BY RANDOM()
LIMIT 30;
"
```

Check: does the assigned family look right for each clause? Aim for ≥27/30 correct. If a family is consistently wrong, file an issue; the fix belongs in a follow-up task, not this one.

- [ ] **Step 17.8: Commit a VERIFIED.md**

```bash
cat > VERIFIED.md << 'EOF'
# Ingestion Phase Verification — [YYYY-MM-DD]

- Contracts ingested: [N]
- Clauses indexed: [N]
- Family distribution: [paste]
- Manual accuracy spot-check: [X]/30 correct
- OpenSearch count matches Postgres: yes/no
EOF
git add VERIFIED.md
git commit -m "docs: verified ingestion against seed corpus"
```

---

## Self-Review (Per writing-plans skill)

### Spec coverage check

| Consolidated plan section | Implemented in |
|---|---|
| §4.1 Embeddings (text-embedding-3-large, 3072-dim) | Task 12 |
| §4.2 Classification (gpt-5-mini, closed taxonomy, cached) | Tasks 11, 14 (caching is planned for Phase 2 — see gap below) |
| §4.4 Search engine (OpenSearch) | Task 5 |
| §4.5 Extraction (PyMuPDF + python-docx) | Tasks 7, 8 |
| §4.6 Segmentation (structure-aware, subclause-preserving) | Task 9 |
| §6 Data model | Tasks 3, 4, 13 |
| §7 20-family taxonomy | Task 11 |
| §11 Risks: checksum dedup | Task 13 |
| §11 Risks: Postgres → OpenSearch ordering | Task 13 (Postgres flush before OS index) |
| Build priority 1–7 (from §10) | Tasks 1–13 |

### Gap identified during self-review

**Classification caching by clause checksum** (consolidated plan §4.2) is *not* implemented in Task 11. Current impl calls the OpenAI API for every clause every time. This is fine for MVP but should be a follow-up. Adding a note here rather than inflating this plan.

### Type/naming consistency check

- `ClauseFamily` enum used in taxonomy.py, classifier.py, orchestrator.py — consistent. ✓
- `IngestPayload`/`ClausePayload` defined in persistence.py, referenced in orchestrator.py — consistent. ✓
- `SegmenterBlock`/`SegmentedClause` defined in segmenter.py — consistent. ✓

### Placeholders scan

No `TBD`, `TODO`, "implement later", or "add error handling" patterns found.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-19-precedentiq-mvp-ingestion.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Plans B (Retrieval) and C (Evaluation harness) will follow after Plan A is executed and verified.

Which approach for Plan A?
