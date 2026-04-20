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


def _payload(contract_id: str, checksum: str, clauses: list[ClausePayload] | None = None) -> IngestPayload:
    return IngestPayload(
        contract_id=contract_id,
        title="Test MSA",
        agreement_type="SaaS_MSA",
        executed_status="executed",
        governing_law="New York",
        client_name=None,
        counterparty_name=None,
        source_file_path=f"/tmp/{contract_id}.pdf",
        source_filename=f"{contract_id}.pdf",
        checksum_sha256=checksum,
        extraction_tool="pymupdf",
        extraction_version="1.24",
        clauses=clauses or [],
    )


def _clause(clause_id: str) -> ClausePayload:
    return ClausePayload(
        clause_id=clause_id,
        section_path="Article 4",
        heading_text="Payment",
        clause_family="payment_terms",
        text_display="Customer shall pay...",
        text_normalized="customer shall pay",
        char_start=0,
        char_end=20,
        embedding=[0.0] * 3072,
    )


def test_persist_writes_contract_and_indexes_clauses(session):
    os_client = MagicMock()
    payload = _payload("ctr_test", "aaa", [_clause("cl_1")])

    persist_ingest(session, os_client, payload)

    contract = session.get(Contract, "ctr_test")
    assert contract is not None
    assert contract.ingest_status == "indexed"
    assert len(contract.clauses) == 1
    os_client.index.assert_called_once()
    call_kwargs = os_client.index.call_args.kwargs
    assert call_kwargs["id"] == "cl_1"
    body = call_kwargs["body"]
    assert body["clause_id"] == "cl_1"
    assert body["contract_id"] == "ctr_test"
    assert body["clause_family"] == "payment_terms"
    assert len(body["embedding"]) == 3072


def test_persist_rejects_duplicate_checksum(session):
    existing = Contract(
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
    payload = _payload("ctr_dup", "same_hash")

    with pytest.raises(ValueError, match="already ingested"):
        persist_ingest(session, os_client, payload)
    os_client.index.assert_not_called()


def test_persist_handles_contract_with_no_clauses(session):
    os_client = MagicMock()
    payload = _payload("ctr_empty", "bbb", clauses=[])

    persist_ingest(session, os_client, payload)

    contract = session.get(Contract, "ctr_empty")
    assert contract is not None
    assert contract.ingest_status == "indexed"
    os_client.index.assert_not_called()
