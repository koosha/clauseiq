import re
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class SegmenterBlock:
    text: str
    kind: Literal["heading", "paragraph"]
    level: int | None = None


@dataclass(frozen=True)
class SegmentedClause:
    heading_text: str | None
    section_path: str | None
    text_display: str
    char_start: int
    char_end: int


SUBCLAUSE_MARKER = re.compile(r"^\s*(\([a-zA-Z0-9]+\)|\d+(\.\d+)*\.)\s+")


def segment_clauses(blocks: list[SegmenterBlock]) -> list[SegmentedClause]:
    clauses: list[SegmentedClause] = []
    heading_stack: list[str] = []
    current_heading: str | None = None
    char_cursor = 0

    for block in blocks:
        if block.kind == "heading":
            if block.level is not None and block.level > 0:
                while len(heading_stack) >= block.level:
                    heading_stack.pop()
                heading_stack.append(block.text)
                current_heading = block.text
            else:
                current_heading = block.text
            char_cursor += len(block.text) + 1
            continue

        section_path = " › ".join(heading_stack) if heading_stack else None
        text = block.text.strip()
        start = char_cursor
        end = char_cursor + len(text)
        char_cursor = end + 1

        clauses.append(
            SegmentedClause(
                heading_text=current_heading,
                section_path=section_path,
                text_display=text,
                char_start=start,
                char_end=end,
            )
        )

    return clauses
