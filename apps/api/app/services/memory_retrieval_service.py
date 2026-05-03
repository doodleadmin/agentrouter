"""Memory retrieval service using deterministic embeddings + similarity ranking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory_chunk import MemoryChunk
from app.models.memory_document import MemoryDocument
from app.services.memory_embedding_service import (
    DeterministicEmbeddingProvider,
    EmbeddingProvider,
    cosine_similarity,
)


@dataclass(slots=True)
class RetrievalItem:
    path: str
    title: str | None
    scope: str
    project_slug: str | None
    heading: str | None
    chunk_index: int
    content: str
    score: float


@dataclass(slots=True)
class RetrievalChunkRecord:
    path: str
    title: str | None
    scope: str
    project_slug: str | None
    heading: str | None
    chunk_index: int
    content: str
    embedding: list[float] | None


class RetrievalRepository(Protocol):
    async def list_chunk_records(
        self,
        *,
        project_slug: str | None,
        scope: list[str] | None,
        limit: int,
    ) -> list[RetrievalChunkRecord]:
        """Return candidate chunk records for ranking."""


class SqlAlchemyRetrievalRepository:
    """DB-backed retrieval repository for candidate loading."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_chunk_records(
        self,
        *,
        project_slug: str | None,
        scope: list[str] | None,
        limit: int,
    ) -> list[RetrievalChunkRecord]:
        stmt = (
            select(MemoryChunk, MemoryDocument)
            .join(MemoryDocument, MemoryChunk.document_id == MemoryDocument.id)
            .where(MemoryChunk.embedding.is_not(None))
            .order_by(MemoryDocument.updated_at.desc())
        )

        if project_slug:
            stmt = stmt.where(MemoryChunk.chunk_metadata["project_slug"].astext == project_slug)
        if scope:
            stmt = stmt.where(MemoryDocument.scope.in_(scope))

        # pull wider candidate set for application-level ranking
        stmt = stmt.limit(max(limit * 8, 50))
        rows = (await self._session.execute(stmt)).all()

        result: list[RetrievalChunkRecord] = []
        for chunk, doc in rows:
            md = chunk.chunk_metadata or {}
            result.append(
                RetrievalChunkRecord(
                    path=doc.path,
                    title=doc.title,
                    scope=doc.scope,
                    project_slug=md.get("project_slug"),
                    heading=md.get("heading"),
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    embedding=chunk.embedding,
                )
            )
        return result


class MemoryRetrievalService:
    """Semantic-like retrieval based on deterministic embeddings."""

    def __init__(
        self,
        repository: RetrievalRepository,
        *,
        embedder: EmbeddingProvider | None = None,
    ) -> None:
        self._repository = repository
        self._embedder = embedder or DeterministicEmbeddingProvider(dimension=1536)

    async def search(
        self,
        *,
        query: str,
        project_slug: str | None = None,
        limit: int = 5,
        scope: list[str] | None = None,
    ) -> list[RetrievalItem]:
        if limit <= 0:
            return []

        query_embedding = self._embedder.embed(query)
        candidates = await self._repository.list_chunk_records(
            project_slug=project_slug,
            scope=scope,
            limit=limit,
        )

        scored: list[RetrievalItem] = []
        for c in candidates:
            if not c.embedding:
                continue
            score = cosine_similarity(query_embedding, c.embedding)
            scored.append(
                RetrievalItem(
                    path=c.path,
                    title=c.title,
                    scope=c.scope,
                    project_slug=c.project_slug,
                    heading=c.heading,
                    chunk_index=c.chunk_index,
                    content=c.content,
                    score=score,
                )
            )

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:limit]
