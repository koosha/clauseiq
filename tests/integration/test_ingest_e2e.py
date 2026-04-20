"""End-to-end ingestion test using live Postgres and OpenSearch via testcontainers.

Skipped when Docker is not available on the host.
"""
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from opensearchpy import OpenSearch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models import Base
from app.ingest.classifier import ClauseClassification
from app.ingest.taxonomy import ClauseFamily


FIXTURES = Path(__file__).parent.parent / "fixtures"

pytestmark = pytest.mark.integration

# Index name matches the default from Settings.opensearch_clauses_index
_INDEX = "clauses"


@pytest.fixture(scope="session")
def pg_url():
    try:
        from testcontainers.postgres import PostgresContainer
    except Exception as e:
        pytest.skip(f"testcontainers not importable: {e}")

    try:
        with PostgresContainer("postgres:16") as pg:
            raw = pg.get_connection_url()
            # Switch from psycopg2 (testcontainers default) to psycopg3 driver
            yield raw.replace("postgresql+psycopg2", "postgresql+psycopg")
    except Exception as e:
        pytest.skip(f"Docker / Postgres container unavailable: {e}")


@pytest.fixture(scope="session")
def os_endpoint():
    try:
        from testcontainers.opensearch import OpenSearchContainer
    except Exception as e:
        pytest.skip(f"testcontainers[opensearch] not importable: {e}")

    try:
        with OpenSearchContainer("opensearchproject/opensearch:2.15.0") as c:
            cfg = c.get_config()
            yield cfg
    except Exception as e:
        pytest.skip(f"Docker / OpenSearch container unavailable: {e}")


@pytest.fixture()
def db_session(pg_url: str):
    engine = create_engine(pg_url)
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as s:
            yield s
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def os_client(os_endpoint: dict):
    client = OpenSearch(
        hosts=[{"host": os_endpoint["host"], "port": int(os_endpoint["port"])}],
        http_auth=(os_endpoint["username"], os_endpoint["password"]),
        use_ssl=False,
        verify_certs=False,
    )
    if not client.indices.exists(index=_INDEX):
        from app.search.index_mapping import CLAUSES_INDEX_BODY

        client.indices.create(index=_INDEX, body=CLAUSES_INDEX_BODY)
    try:
        yield client
    finally:
        client.indices.delete(index=_INDEX, ignore=[404])


def _make_settings_patch(pg_url: str, os_host: str, os_port: str) -> dict:
    """Return env-var overrides so get_settings() resolves without a .env file."""
    return {
        "DATABASE_URL": pg_url,
        "OPENSEARCH_URL": f"http://{os_host}:{os_port}",
        "OPENAI_API_KEY": "test-key-not-used",
    }


@patch("app.ingest.orchestrator.classify_clause")
@patch("app.ingest.orchestrator.embed_texts")
def test_full_pipeline_pdf(
    mock_embed,
    mock_classify,
    db_session: Session,
    os_client: OpenSearch,
    pg_url: str,
    os_endpoint: dict,
):
    mock_classify.return_value = ClauseClassification(
        family=ClauseFamily.PAYMENT_TERMS, confidence="high", rationale="test"
    )
    mock_embed.side_effect = lambda texts: [[0.0] * 3072] * len(texts)

    env_patch = _make_settings_patch(pg_url, os_endpoint["host"], os_endpoint["port"])
    with patch.dict(os.environ, env_patch):
        # Clear lru_cache so get_settings() picks up the patched env vars
        from app.config import get_settings

        get_settings.cache_clear()

        from app.ingest.orchestrator import ingest_contract

        contract_id = ingest_contract(db_session, os_client, FIXTURES / "sample.pdf")

    get_settings.cache_clear()

    assert contract_id is not None

    os_client.indices.refresh(index=_INDEX)
    resp = os_client.search(
        index=_INDEX,
        body={"query": {"term": {"contract_id": contract_id}}},
    )
    assert resp["hits"]["total"]["value"] >= 1


@patch("app.ingest.orchestrator.classify_clause")
@patch("app.ingest.orchestrator.embed_texts")
def test_full_pipeline_docx(
    mock_embed,
    mock_classify,
    db_session: Session,
    os_client: OpenSearch,
    pg_url: str,
    os_endpoint: dict,
):
    mock_classify.return_value = ClauseClassification(
        family=ClauseFamily.DEFINITIONS, confidence="medium", rationale="test"
    )
    mock_embed.side_effect = lambda texts: [[0.0] * 3072] * len(texts)

    env_patch = _make_settings_patch(pg_url, os_endpoint["host"], os_endpoint["port"])
    with patch.dict(os.environ, env_patch):
        from app.config import get_settings

        get_settings.cache_clear()

        from app.ingest.orchestrator import ingest_contract

        contract_id = ingest_contract(db_session, os_client, FIXTURES / "sample.docx")

    get_settings.cache_clear()

    assert contract_id is not None
    os_client.indices.refresh(index=_INDEX)
    resp = os_client.search(
        index=_INDEX,
        body={"query": {"term": {"contract_id": contract_id}}},
    )
    assert resp["hits"]["total"]["value"] >= 1
