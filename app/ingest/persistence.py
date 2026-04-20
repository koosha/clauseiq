from dataclasses import dataclass
from datetime import datetime, timezone
from opensearchpy import OpenSearch
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import get_settings
from app.db.models import Contract, Clause


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
        raise ValueError(
            f"Contract already ingested (checksum {payload.checksum_sha256})"
        )

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
