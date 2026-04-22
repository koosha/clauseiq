"""Wire the ingestion stages together into a single end-to-end pipeline.

Order of operations per contract:
    1. intake_file            (read bytes, compute checksum)
    2. extract_pdf / _docx    (layout-aware text extraction)
    3. extract_contract_metadata  (agreement_type, governing_law, executed_status)
    4. segment_clauses        (structure-aware clause boundaries)
    5. embed_texts            (OpenAI embeddings, one per clause)
    6. classify_clause        (OpenAI structured output, one per clause)
    7. persist_ingest         (Postgres write + OpenSearch index)
"""

import re
import uuid
from pathlib import Path
from typing import Literal

from opensearchpy import OpenSearch
from sqlalchemy.orm import Session

from app.ingest.classifier import classify_clause
from app.ingest.embedder import embed_texts
from app.ingest.extractors.docx import extract_docx
from app.ingest.extractors.pdf import extract_pdf
from app.ingest.intake import intake_file
from app.ingest.metadata import extract_contract_metadata
from app.ingest.persistence import ClausePayload, IngestPayload, persist_ingest
from app.ingest.segmenter import SegmenterBlock, segment_clauses

# Matches lines like "1. Payment Terms" or "2.3. Renewal". Used as a cheap
# heading heuristic when a PDF has no style metadata.
HEADING_LINE = re.compile(r"^\s*\d+(?:\.\d+)*\.\s+[A-Z]")


def _blocks_from_pdf(path: Path) -> tuple[list[SegmenterBlock], str, str, str]:
    result = extract_pdf(path)
    blocks: list[SegmenterBlock] = []
    for line in result.text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if HEADING_LINE.match(stripped):
            blocks.append(SegmenterBlock(text=stripped, kind="heading", level=1))
        else:
            blocks.append(SegmenterBlock(text=stripped, kind="paragraph"))
    return blocks, result.text, result.extraction_tool, result.extraction_version


def _blocks_from_docx(path: Path) -> tuple[list[SegmenterBlock], str, str, str]:
    result = extract_docx(path)
    blocks: list[SegmenterBlock] = []
    joined: list[str] = []
    for b in result.blocks:
        kind: Literal["heading", "paragraph"] = "heading" if b.style.startswith("Heading") else "paragraph"
        blocks.append(SegmenterBlock(text=b.text, kind=kind, level=b.level))
        joined.append(b.text)
    return blocks, "\n".join(joined), result.extraction_tool, result.extraction_version


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def ingest_contract(
    session: Session,
    os_client: OpenSearch,
    file_path: Path,
) -> str:
    """Run the full ingestion pipeline on a single contract file.

    Returns the generated contract_id. Raises ValueError if the file extension
    is unsupported or if the checksum matches a contract already in the DB.
    """
    intake = intake_file(file_path)

    if intake.file_extension == ".pdf":
        blocks, full_text, tool, version = _blocks_from_pdf(file_path)
    elif intake.file_extension == ".docx":
        blocks, full_text, tool, version = _blocks_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {intake.file_extension}")

    metadata = extract_contract_metadata(full_text)
    segments = segment_clauses(blocks)

    clause_texts = [segment.text_display for segment in segments]
    embeddings = embed_texts(clause_texts)

    classifications = [
        classify_clause(
            heading_text=segment.heading_text,
            section_path=segment.section_path,
            clause_text=segment.text_display,
        )
        for segment in segments
    ]

    contract_id = f"ctr_{uuid.uuid4().hex[:12]}"

    clause_payloads: list[ClausePayload] = []
    for segment, classification, embedding in zip(
        segments, classifications, embeddings, strict=True
    ):
        clause_payloads.append(
            ClausePayload(
                clause_id=f"cl_{uuid.uuid4().hex[:12]}",
                section_path=segment.section_path,
                heading_text=segment.heading_text,
                clause_family=(
                    classification.family.value
                    if classification.family is not None
                    else None
                ),
                text_display=segment.text_display,
                text_normalized=_normalize_text(segment.text_display),
                char_start=segment.char_start,
                char_end=segment.char_end,
                embedding=embedding,
            )
        )

    payload = IngestPayload(
        contract_id=contract_id,
        title=intake.source_filename.rsplit(".", 1)[0],
        agreement_type=metadata.agreement_type or "SaaS_MSA",
        executed_status=metadata.executed_status or "unknown",
        governing_law=metadata.governing_law,
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
