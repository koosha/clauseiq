from pathlib import Path
from app.ingest.extractors.docx import extract_docx


FIXTURES = Path(__file__).parent.parent.parent / "fixtures"


def test_extract_docx_returns_structured_blocks():
    result = extract_docx(FIXTURES / "sample.docx")
    headings = [b for b in result.blocks if b.style.startswith("Heading")]
    paragraphs = [b for b in result.blocks if b.style == "Normal"]

    assert any("Definitions" in b.text for b in headings)
    assert any("Payment Terms" in b.text for b in headings)
    assert any("undisputed invoices" in b.text for b in paragraphs)
    assert result.extraction_tool == "python-docx"
