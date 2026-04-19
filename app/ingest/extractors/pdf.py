from dataclasses import dataclass
from pathlib import Path
import fitz  # PyMuPDF


class PdfExtractionError(Exception):
    pass


@dataclass(frozen=True)
class PdfExtractionResult:
    text: str
    page_count: int
    page_offsets: list[int]
    extraction_tool: str
    extraction_version: str


MIN_TEXT_CHARS_PER_PAGE = 50


def extract_pdf(path: Path) -> PdfExtractionResult:
    doc = fitz.open(path)
    try:
        pages: list[str] = []
        offsets: list[int] = []
        total_chars = 0

        for page in doc:
            offsets.append(total_chars)
            page_text = page.get_text("text")
            pages.append(page_text)
            total_chars += len(page_text)

        full_text = "".join(pages)

        avg_chars_per_page = total_chars / max(doc.page_count, 1)
        if avg_chars_per_page < MIN_TEXT_CHARS_PER_PAGE:
            raise PdfExtractionError(
                f"PDF has no text layer (avg {avg_chars_per_page:.0f} chars/page). "
                "Scanned PDFs are not supported in MVP."
            )

        return PdfExtractionResult(
            text=full_text,
            page_count=doc.page_count,
            page_offsets=offsets,
            extraction_tool="pymupdf",
            extraction_version=fitz.VersionBind,
        )
    finally:
        doc.close()
