from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.models import Base, Contract, Clause


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
