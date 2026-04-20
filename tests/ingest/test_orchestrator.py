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

    # Return enough embeddings for however many clauses come out of the sample PDF
    mock_embed.side_effect = lambda texts: [[0.0] * 3072] * len(texts)
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
    # every clause has an embedding and a family
    for c in contract.clauses:
        assert c.embedding is not None
        assert c.clause_family == "payment_terms"


@patch("app.ingest.orchestrator.classify_clause")
@patch("app.ingest.orchestrator.embed_texts")
def test_ingest_docx_end_to_end(mock_embed, mock_classify, session):
    from app.ingest.classifier import ClauseClassification
    from app.ingest.taxonomy import ClauseFamily

    mock_embed.side_effect = lambda texts: [[0.0] * 3072] * len(texts)
    mock_classify.return_value = ClauseClassification(
        family=ClauseFamily.DEFINITIONS,
        confidence="medium",
        rationale="ok",
    )
    os_client = MagicMock()

    contract_id = ingest_contract(
        session=session,
        os_client=os_client,
        file_path=FIXTURES / "sample.docx",
    )

    assert contract_id is not None
    contract = session.get(Contract, contract_id)
    assert contract is not None
    assert contract.ingest_status == "indexed"
    assert len(contract.clauses) >= 1


def test_ingest_rejects_unsupported_file(session, tmp_path):
    os_client = MagicMock()
    bad = tmp_path / "notes.txt"
    bad.write_text("hello")

    with pytest.raises(ValueError):
        ingest_contract(session=session, os_client=os_client, file_path=bad)
