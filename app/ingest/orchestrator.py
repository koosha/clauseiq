import re
import uuid
from pathlib import Path
from typing import Literal

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
    intake = intake_file(file_path)

    if intake.file_extension == ".pdf":
        blocks, full_text, tool, version = _blocks_from_pdf(file_path)
    elif intake.file_extension == ".docx":
        blocks, full_text, tool, version = _blocks_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {intake.file_extension}")

    md = extract_contract_metadata(full_text)
    segments = segment_clauses(blocks)

    clause_texts = [seg.text_display for seg in segments]
    embeddings = embed_texts(clause_texts)

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
                clause_family=cls.family.value if cls.family is not None else None,
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
