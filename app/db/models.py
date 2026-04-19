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
