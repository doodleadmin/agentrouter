"""Memory indexing service for .ai_memory markdown vault."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.memory_chunk import MemoryChunk
from app.models.memory_document import MemoryDocument
from app.models.project import Project
from app.services.memory_chunking_service import MemoryChunkingService
from app.services.memory_embedding_service import (
    DeterministicEmbeddingProvider,
    EmbeddingProvider,
)


@dataclass(slots=True)
class MemoryReindexResult:
    indexed_documents: int = 0
    skipped_documents: int = 0
    total_chunks: int = 0
    scanned_files: int = 0


class MemoryIndexingService:
    """Indexes markdown documents into memory_documents + memory_chunks."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        vault_path: str | None = None,
        chunker: MemoryChunkingService | None = None,
        embedder: EmbeddingProvider | None = None,
    ) -> None:
        self._session = session
        self._vault = Path(vault_path or settings.MEMORY_VAULT_PATH).resolve()
        self._chunker = chunker or MemoryChunkingService()
        self._embedder = embedder or DeterministicEmbeddingProvider(dimension=1536)

    async def reindex(self, *, scope: str = "all", project_slug: str | None = None) -> MemoryReindexResult:
        files = self._discover_files(scope=scope, project_slug=project_slug)
        result = MemoryReindexResult(scanned_files=len(files))

        project_map = await self._load_project_map()

        for filepath in files:
            relative_path = filepath.relative_to(self._vault).as_posix()
            content = filepath.read_text(encoding="utf-8")
            content_hash = _sha256_text(content)

            path_scope, path_project_slug = _resolve_scope(relative_path)
            pid = project_map.get(path_project_slug) if path_project_slug else None
            title = _extract_title(content, filepath.stem)

            existing = await self._get_document_by_path(relative_path)
            if existing and existing.content_hash == content_hash:
                result.skipped_documents += 1
                continue

            if existing is None:
                existing = MemoryDocument(
                    scope=path_scope,
                    project_id=pid,
                    path=relative_path,
                    title=title,
                    content=content,
                    content_hash=content_hash,
                )
                self._session.add(existing)
                await self._session.flush()
            else:
                existing.scope = path_scope
                existing.project_id = pid
                existing.title = title
                existing.content = content
                existing.content_hash = content_hash
                await self._session.flush()

            # Safe replacement: delete old chunks then insert new ones
            await self._session.execute(
                delete(MemoryChunk).where(MemoryChunk.document_id == existing.id)
            )

            drafts = self._chunker.chunk_markdown(content)
            for draft in drafts:
                metadata = {
                    "path": relative_path,
                    "title": title,
                    "scope": path_scope,
                    "project_slug": path_project_slug,
                    "heading": draft.heading,
                }
                chunk = MemoryChunk(
                    document_id=existing.id,
                    project_id=pid,
                    chunk_index=draft.chunk_index,
                    content=draft.content,
                    embedding=self._embedder.embed(draft.content),
                    chunk_metadata=metadata,
                )
                self._session.add(chunk)

            result.indexed_documents += 1
            result.total_chunks += len(drafts)

        await self._session.commit()
        return result

    def _discover_files(self, *, scope: str, project_slug: str | None) -> list[Path]:
        if scope not in {"all", "global", "project", "tasks", "decisions", "agents"}:
            raise ValueError(f"Unsupported scope: {scope}")

        if scope == "project":
            if not project_slug:
                return []
            root = self._vault / "projects" / project_slug
            return self._safe_markdown_files(root)

        if scope == "global":
            files = []
            for candidate in ["README.md", "_INDEX.md", "current_state.md", "agent_mission_control_pipeline.md"]:
                p = self._vault / candidate
                if p.is_file():
                    files.append(p)
            return files

        if scope == "tasks":
            return self._safe_markdown_files(self._vault / "tasks")
        if scope == "decisions":
            return self._safe_markdown_files(self._vault / "decisions")
        if scope == "agents":
            return self._safe_markdown_files(self._vault / "agents")

        # all
        return self._safe_markdown_files(self._vault)

    def _safe_markdown_files(self, root: Path) -> list[Path]:
        if not root.exists() or not root.is_dir():
            return []

        files: list[Path] = []
        for file in root.rglob("*.md"):
            resolved = file.resolve()
            try:
                resolved.relative_to(self._vault)
            except ValueError:
                continue

            rel_parts = resolved.relative_to(self._vault).parts
            if any(part.startswith(".") for part in rel_parts):
                # skip .obsidian and hidden
                continue
            files.append(resolved)
        return sorted(files)

    async def _get_document_by_path(self, path: str) -> MemoryDocument | None:
        stmt = select(MemoryDocument).where(MemoryDocument.path == path)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def _load_project_map(self) -> dict[str, str]:
        stmt = select(Project.slug, Project.id)
        rows = (await self._session.execute(stmt)).all()
        return {slug: str(pid) for slug, pid in rows}


def _sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _extract_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            if title:
                return title
    return fallback


def _resolve_scope(relative_path: str) -> tuple[str, str | None]:
    parts = relative_path.split("/")
    if parts[0] == "projects" and len(parts) >= 2:
        return "project", parts[1]
    if parts[0] == "tasks":
        return "task", None
    if parts[0] == "decisions":
        return "decision", None
    if parts[0] == "agents":
        return "agent", None
    return "global", None
