from dataclasses import dataclass
from pathlib import Path
import docx


@dataclass(frozen=True)
class DocxBlock:
    text: str
    style: str
    level: int | None


@dataclass(frozen=True)
class DocxExtractionResult:
    blocks: list[DocxBlock]
    extraction_tool: str
    extraction_version: str


def extract_docx(path: Path) -> DocxExtractionResult:
    doc = docx.Document(str(path))
    blocks: list[DocxBlock] = []

    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        style_name = p.style.name if p.style else "Normal"
        level = None
        if style_name.startswith("Heading "):
            try:
                level = int(style_name.split()[1])
            except (IndexError, ValueError):
                level = None
        blocks.append(DocxBlock(text=text, style=style_name, level=level))

    return DocxExtractionResult(
        blocks=blocks,
        extraction_tool="python-docx",
        extraction_version=docx.__version__,
    )
