"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-19
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contracts",
        sa.Column("contract_id", sa.String(64), primary_key=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("agreement_type", sa.String(64), nullable=False),
        sa.Column("executed_status", sa.String(32), nullable=False),
        sa.Column("governing_law", sa.String(128), nullable=True),
        sa.Column("client_name", sa.String(256), nullable=True),
        sa.Column("counterparty_name", sa.String(256), nullable=True),
        sa.Column("source_file_path", sa.Text, nullable=False),
        sa.Column("source_filename", sa.String(512), nullable=False),
        sa.Column("checksum_sha256", sa.String(64), nullable=False, unique=True),
        sa.Column("extraction_tool", sa.String(64), nullable=False),
        sa.Column("extraction_version", sa.String(32), nullable=False),
        sa.Column("ingest_status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "clauses",
        sa.Column("clause_id", sa.String(64), primary_key=True),
        sa.Column("contract_id", sa.String(64), sa.ForeignKey("contracts.contract_id"), nullable=False),
        sa.Column("section_path", sa.String(512), nullable=True),
        sa.Column("heading_text", sa.String(512), nullable=True),
        sa.Column("clause_family", sa.String(64), nullable=True),
        sa.Column("text_display", sa.Text, nullable=False),
        sa.Column("text_normalized", sa.Text, nullable=False),
        sa.Column("char_start", sa.Integer, nullable=True),
        sa.Column("char_end", sa.Integer, nullable=True),
        sa.Column("embedding", sa.JSON, nullable=True),
        sa.Column("embedding_model", sa.String(64), nullable=False),
        sa.Column("embedding_version", sa.String(32), nullable=False),
        sa.Column("embedding_created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("language", sa.String(8), nullable=False),
        sa.Column("jurisdiction", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "metadata_confidence",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("record_id", sa.String(64), nullable=False),
        sa.Column("record_type", sa.String(16), nullable=False),
        sa.Column("field_name", sa.String(64), nullable=False),
        sa.Column("value", sa.Text, nullable=True),
        sa.Column("confidence", sa.String(16), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("metadata_confidence")
    op.drop_table("clauses")
    op.drop_table("contracts")
