from pathlib import Path
import pytest
from app.ingest.intake import intake_file, IntakeResult


def test_intake_produces_checksum_and_metadata(tmp_path: Path):
    f = tmp_path / "sample.pdf"
    f.write_bytes(b"%PDF-1.4 minimal contents")

    result: IntakeResult = intake_file(f)

    assert result.checksum_sha256 is not None
    assert len(result.checksum_sha256) == 64
    assert result.source_filename == "sample.pdf"
    assert result.source_file_path == str(f)
    assert result.file_extension == ".pdf"


def test_intake_detects_docx(tmp_path: Path):
    f = tmp_path / "X.docx"
    f.write_bytes(b"PK\x03\x04 fake zip")
    result = intake_file(f)
    assert result.file_extension == ".docx"


def test_intake_rejects_unsupported_extension(tmp_path: Path):
    f = tmp_path / "notes.txt"
    f.write_text("hello")
    with pytest.raises(ValueError, match="Unsupported file type"):
        intake_file(f)
