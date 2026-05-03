"""Memory markdown chunking service."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MemoryChunkDraft:
    """In-memory chunk representation before DB persistence."""

    chunk_index: int
    content: str
    heading: str | None


class MemoryChunkingService:
    """Splits markdown into semantically stable chunks.

    Strategy:
    1. Split by markdown headings (# .. ######).
    2. Merge adjacent sections into chunks up to max_chars.
    3. If one section is too large, split by paragraph/line boundaries.
    """

    def __init__(self, *, max_chars: int = 1200) -> None:
        self.max_chars = max_chars

    def chunk_markdown(self, markdown: str) -> list[MemoryChunkDraft]:
        """Split markdown into chunk drafts."""
        if not markdown.strip():
            return []

        sections = self._split_sections(markdown)
        chunks: list[tuple[str, str | None]] = []

        for heading, section_text in sections:
            if len(section_text) <= self.max_chars:
                chunks.append((section_text, heading))
                continue

            for part in self._split_large_text(section_text):
                chunks.append((part, heading))

        return [
            MemoryChunkDraft(chunk_index=i, content=text, heading=heading)
            for i, (text, heading) in enumerate(chunks)
            if text.strip()
        ]

    def _split_sections(self, markdown: str) -> list[tuple[str | None, str]]:
        lines = markdown.splitlines()
        sections: list[tuple[str | None, list[str]]] = []

        current_heading: str | None = None
        current_lines: list[str] = []

        for line in lines:
            if self._is_heading(line):
                if current_lines:
                    sections.append((current_heading, current_lines))
                current_heading = line.lstrip("#").strip() or None
                current_lines = [line]
            else:
                current_lines.append(line)

        if current_lines:
            sections.append((current_heading, current_lines))

        return [(heading, "\n".join(body).strip()) for heading, body in sections if "\n".join(body).strip()]

    @staticmethod
    def _is_heading(line: str) -> bool:
        stripped = line.strip()
        if not stripped.startswith("#"):
            return False
        level = 0
        for ch in stripped:
            if ch == "#":
                level += 1
            else:
                break
        return 1 <= level <= 6 and len(stripped) > level and stripped[level] == " "

    def _split_large_text(self, text: str) -> list[str]:
        paragraphs = [p for p in text.split("\n\n") if p.strip()]
        if len(paragraphs) == 1:
            return self._split_by_line_length(text)

        chunks: list[str] = []
        buffer = ""

        for p in paragraphs:
            candidate = f"{buffer}\n\n{p}".strip() if buffer else p
            if len(candidate) <= self.max_chars:
                buffer = candidate
            else:
                if buffer:
                    chunks.append(buffer)
                if len(p) <= self.max_chars:
                    buffer = p
                else:
                    chunks.extend(self._split_by_line_length(p))
                    buffer = ""

        if buffer:
            chunks.append(buffer)

        return chunks

    def _split_by_line_length(self, text: str) -> list[str]:
        lines = text.splitlines()
        chunks: list[str] = []
        buffer = ""

        for line in lines:
            candidate = f"{buffer}\n{line}".strip() if buffer else line
            if len(candidate) <= self.max_chars:
                buffer = candidate
            else:
                if buffer:
                    chunks.append(buffer)
                # fall back to hard split if one line itself is huge
                if len(line) <= self.max_chars:
                    buffer = line
                else:
                    for start in range(0, len(line), self.max_chars):
                        chunks.append(line[start : start + self.max_chars])
                    buffer = ""

        if buffer:
            chunks.append(buffer)

        return chunks
