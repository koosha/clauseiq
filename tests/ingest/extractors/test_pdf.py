from pathlib import Path
import pytest
from app.ingest.extractors.pdf import extract_pdf, PdfExtractionError


FIXTURES = Path(__file__).parent.parent.parent / "fixtures"


def test_extract_pdf_returns_text_and_page_offsets():
    result = extract_pdf(FIXTURES / "sample.pdf")
    assert "Payment Terms" in result.text
    assert "undisputed invoices" in result.text
    assert result.page_count == 1
    assert result.extraction_tool == "pymupdf"


def test_extract_pdf_rejects_scanned():
    with pytest.raises(PdfExtractionError, match="no text layer"):
        extract_pdf(FIXTURES / "scanned.pdf")
