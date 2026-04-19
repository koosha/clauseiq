import hashlib
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


@dataclass(frozen=True)
class IntakeResult:
    source_filename: str
    source_file_path: str
    file_extension: str
    checksum_sha256: str
    size_bytes: int


def intake_file(path: Path) -> IntakeResult:
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")

    data = path.read_bytes()
    return IntakeResult(
        source_filename=path.name,
        source_file_path=str(path),
        file_extension=ext,
        checksum_sha256=hashlib.sha256(data).hexdigest(),
        size_bytes=len(data),
    )
