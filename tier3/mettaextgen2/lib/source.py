"""Source documents and provenance spans.

Every Gen2 claim carries a Span into the *raw* source chapter. Spans are only
constructed through SourceDocument.span(), which validates the offsets, so a
module cannot emit a claim without provenance (GEN2_MODULES.md §1.1 rule 3,
§3.1).
"""

from __future__ import annotations

import bisect
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple


class SpanError(ValueError):
    """Raised when a span does not address real, non-empty source text."""


@dataclass(frozen=True)
class Span:
    source_text_id: str
    file: str
    line: int          # 1-based line of char_start
    char_start: int    # offsets into the raw source text, end-exclusive
    char_end: int
    text: str          # exactly raw_text[char_start:char_end]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_text_id": self.source_text_id,
            "file": self.file,
            "line": self.line,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "text": self.text,
        }


@dataclass(frozen=True)
class SourceDocument:
    """A raw source chapter plus the scene region Gen2 is reading."""

    path: Path
    text: str
    sha256: str
    line_offsets: Tuple[int, ...]   # line_offsets[i] = offset where line i+1 starts
    region_first_line: int          # 1-based, inclusive
    region_last_line: int           # 1-based, inclusive

    @classmethod
    def from_file(cls, path: Path, first_line: int, last_line: int) -> "SourceDocument":
        raw_bytes = path.read_bytes()
        text = raw_bytes.decode("utf-8")
        offsets = [0]
        for i, ch in enumerate(text):
            if ch == "\n":
                offsets.append(i + 1)
        line_count = len(text.splitlines())
        if not (1 <= first_line <= last_line <= line_count):
            raise SpanError(
                f"scene region {first_line}-{last_line} outside {path.name} (1-{line_count})"
            )
        return cls(
            path=path,
            text=text,
            sha256=hashlib.sha256(raw_bytes).hexdigest(),
            line_offsets=tuple(offsets),
            region_first_line=first_line,
            region_last_line=last_line,
        )

    @property
    def source_text_id(self) -> str:
        return f"{self.path.name}@{self.sha256}"

    def line_start(self, line: int) -> int:
        return self.line_offsets[line - 1]

    def line_end(self, line: int) -> int:
        """Offset just past the line's last character (excluding the newline)."""
        if line < len(self.line_offsets):
            return self.line_offsets[line] - 1
        return len(self.text)

    def line_text(self, line: int) -> str:
        return self.text[self.line_start(line):self.line_end(line)]

    def line_of(self, offset: int) -> int:
        return bisect.bisect_right(self.line_offsets, offset)

    @property
    def region_start(self) -> int:
        return self.line_start(self.region_first_line)

    @property
    def region_end(self) -> int:
        return self.line_end(self.region_last_line)

    def span(self, char_start: int, char_end: int) -> Span:
        if not (0 <= char_start < char_end <= len(self.text)):
            raise SpanError(f"invalid span {char_start}:{char_end}")
        if not (self.region_start <= char_start and char_end <= self.region_end):
            raise SpanError(
                f"span {char_start}:{char_end} outside scene region "
                f"{self.region_start}:{self.region_end}"
            )
        text = self.text[char_start:char_end]
        if not text.strip():
            raise SpanError(f"span {char_start}:{char_end} is blank")
        return Span(
            source_text_id=self.source_text_id,
            file=str(self.path),
            line=self.line_of(char_start),
            char_start=char_start,
            char_end=char_end,
            text=text,
        )

    def line_span(self, line: int) -> Span:
        return self.span(self.line_start(line), self.line_end(line))
