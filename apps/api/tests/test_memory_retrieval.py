"""Tests for memory retrieval service with fake repository."""

from app.services.memory_embedding_service import DeterministicEmbeddingProvider
from app.services.memory_retrieval_service import (
    MemoryRetrievalService,
    RetrievalChunkRecord,
)


class FakeRepo:
    def __init__(self, records: list[RetrievalChunkRecord]) -> None:
        self._records = records

    async def list_chunk_records(self, *, project_slug, scope, limit):
        results = self._records
        if project_slug:
            results = [r for r in results if r.project_slug == project_slug]
        if scope:
            results = [r for r in results if r.scope in scope]
        return results[: max(limit * 8, 50)]


async def test_retrieval_returns_top_k() -> None:
    embedder = DeterministicEmbeddingProvider(dimension=1536)
    q = "how to deploy staging"
    records = [
        RetrievalChunkRecord(
            path="projects/a/deployment.md",
            title="deploy",
            scope="project",
            project_slug="a",
            heading="Staging",
            chunk_index=0,
            content="staging deploy via docker compose",
            embedding=embedder.embed("staging deploy via docker compose"),
        ),
        RetrievalChunkRecord(
            path="tasks/t1.md",
            title="task",
            scope="task",
            project_slug=None,
            heading=None,
            chunk_index=0,
            content="unrelated content",
            embedding=embedder.embed("something different"),
        ),
    ]
    svc = MemoryRetrievalService(FakeRepo(records), embedder=embedder)
    items = await svc.search(query=q, limit=1)
    assert len(items) == 1
    assert items[0].path == "projects/a/deployment.md"


async def test_retrieval_filters_by_project_and_scope() -> None:
    embedder = DeterministicEmbeddingProvider(dimension=1536)
    records = [
        RetrievalChunkRecord(
            path="projects/a/architecture.md",
            title="arch",
            scope="project",
            project_slug="a",
            heading=None,
            chunk_index=0,
            content="service boundaries",
            embedding=embedder.embed("service boundaries"),
        ),
        RetrievalChunkRecord(
            path="projects/b/architecture.md",
            title="arch",
            scope="project",
            project_slug="b",
            heading=None,
            chunk_index=0,
            content="service boundaries",
            embedding=embedder.embed("service boundaries"),
        ),
    ]
    svc = MemoryRetrievalService(FakeRepo(records), embedder=embedder)
    items = await svc.search(query="boundaries", project_slug="a", scope=["project"], limit=5)
    assert len(items) == 1
    assert items[0].project_slug == "a"
