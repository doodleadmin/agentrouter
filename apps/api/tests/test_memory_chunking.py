"""Tests for memory markdown chunking."""

from app.services.memory_chunking_service import MemoryChunkingService


def test_chunk_by_headings() -> None:
    svc = MemoryChunkingService(max_chars=200)
    md = """# Title
intro

## Part A
aaa

## Part B
bbb
"""
    chunks = svc.chunk_markdown(md)
    assert len(chunks) >= 2
    assert chunks[0].heading == "Title"
    assert any(c.heading == "Part A" for c in chunks)


def test_chunk_large_section_split() -> None:
    svc = MemoryChunkingService(max_chars=50)
    md = "# Big\n\n" + ("line\n" * 60)
    chunks = svc.chunk_markdown(md)
    assert len(chunks) > 1
    assert all(len(c.content) <= 50 for c in chunks)


def test_empty_markdown_returns_empty() -> None:
    svc = MemoryChunkingService()
    assert svc.chunk_markdown("   \n\n") == []
