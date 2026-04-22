"""Persist an ingested contract to Postgres and mirror its clauses to OpenSearch.

Postgres is the source of truth; the OpenSearch index is the derived search
surface. Writes go to Postgres first (source of truth), then to OpenSearch
(eventually consistent). Re-ingesting a contract with a known checksum raises
rather than producing a duplicate.
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from opensearchpy import OpenSearch
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import Clause, Contract


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
    """Write the contract and its clauses to Postgres and index them in OpenSearch."""
    settings = get_settings()

    duplicate = session.execute(
        select(Contract).where(Contract.checksum_sha256 == payload.checksum_sha256)
    ).scalar_one_or_none()
    if duplicate is not None:
        raise ValueError(
            f"Contract already ingested (checksum {payload.checksum_sha256})"
        )

    now = datetime.now(timezone.utc)
    embedding_version = now.strftime("%Y-%m")

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

    for payload_clause in payload.clauses:
        clause = Clause(
            clause_id=payload_clause.clause_id,
            contract_id=payload.contract_id,
            section_path=payload_clause.section_path,
            heading_text=payload_clause.heading_text,
            clause_family=payload_clause.clause_family,
            text_display=payload_clause.text_display,
            text_normalized=payload_clause.text_normalized,
            char_start=payload_clause.char_start,
            char_end=payload_clause.char_end,
            embedding=payload_clause.embedding,
            embedding_model=settings.openai_embedding_model,
            embedding_version=embedding_version,
            embedding_created_at=now,
            language="en",
            jurisdiction=None,
            created_at=now,
        )
        session.add(clause)

    session.flush()

    for payload_clause in payload.clauses:
        os_client.index(
            index=settings.opensearch_clauses_index,
            id=payload_clause.clause_id,
            body={
                "clause_id": payload_clause.clause_id,
                "contract_id": payload.contract_id,
                "agreement_type": payload.agreement_type,
                "clause_family": payload_clause.clause_family,
                "governing_law": payload.governing_law,
                "section_path": payload_clause.section_path,
                "heading_text": payload_clause.heading_text,
                "text_display": payload_clause.text_display,
                "text_normalized": payload_clause.text_normalized,
                "embedding": payload_clause.embedding,
            },
        )

    contract.ingest_status = "indexed"
    session.commit()
