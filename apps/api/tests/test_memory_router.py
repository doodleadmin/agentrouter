"""Tests for memory router — HTTP endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_async_session
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a test client with a temp vault."""
    vault = tmp_path / ".ai_memory"
    vault.mkdir()
    (vault / "projects" / "demo-app").mkdir(parents=True)
    (vault / "tasks").mkdir()
    (vault / "templates").mkdir()
    (vault / "decisions").mkdir()

    # Seed files
    (vault / "current_state.md").write_text("# State\n", encoding="utf-8")
    (vault / "projects" / "demo-app" / "agent_notes.md").write_text(
        "# Notes\n", encoding="utf-8"
    )
    (vault / "projects" / "demo-app" / "overview.md").write_text(
        "# Demo\n", encoding="utf-8"
    )
    (vault / "tasks" / "task-001.md").write_text("# Task\n", encoding="utf-8")

    # Patch settings
    monkeypatch.setattr("app.config.settings.MEMORY_VAULT_PATH", str(vault))

    async def _fake_session():
        yield object()

    app.dependency_overrides[get_async_session] = _fake_session
    tc = TestClient(app)
    try:
        yield tc
    finally:
        app.dependency_overrides.clear()


class TestListFiles:
    def test_list_all(self, client: TestClient) -> None:
        resp = client.get("/memory/files")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 3

    def test_list_by_project(self, client: TestClient) -> None:
        resp = client.get("/memory/files?project_slug=demo-app")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_slug"] == "demo-app"
        assert any("overview.md" in f for f in data["files"])

    def test_list_by_prefix(self, client: TestClient) -> None:
        resp = client.get("/memory/files?prefix=tasks")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1


class TestReadFile:
    def test_read_existing(self, client: TestClient) -> None:
        resp = client.get("/memory/files/current_state.md")
        assert resp.status_code == 200
        data = resp.json()
        assert data["path"] == "current_state.md"
        assert "# State" in data["content"]

    def test_read_nested(self, client: TestClient) -> None:
        resp = client.get("/memory/files/projects/demo-app/overview.md")
        assert resp.status_code == 200
        assert "Demo" in resp.json()["content"]

    def test_read_not_found(self, client: TestClient) -> None:
        resp = client.get("/memory/files/nonexistent.md")
        assert resp.status_code == 404

    def test_read_invalid_path(self, client: TestClient) -> None:
        resp = client.get("/memory/files/C:\\secret.md")
        assert resp.status_code == 400


class TestWriteFile:
    def test_write_free_file(self, client: TestClient) -> None:
        resp = client.put(
            "/memory/files/tasks/new-task.md",
            json={"content": "# New Task\n"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "written"
        assert data["access_tier"] == "free"

    def test_write_approval_required_without_bypass(self, client: TestClient) -> None:
        resp = client.put(
            "/memory/files/current_state.md",
            json={"content": "# Updated State\n"},
        )
        assert resp.status_code == 403

    def test_write_approval_required_with_bypass(self, client: TestClient) -> None:
        resp = client.put(
            "/memory/files/current_state.md?bypass_approval=true",
            json={"content": "# Updated State\n"},
        )
        assert resp.status_code == 200

    def test_write_secrets_blocked(self, client: TestClient) -> None:
        resp = client.put(
            "/memory/files/tasks/test.md",
            json={"content": "password=secret123"},
        )
        assert resp.status_code == 422

    def test_write_forbidden_path(self, client: TestClient) -> None:
        resp = client.put(
            "/memory/files/templates/test.md",
            json={"content": "template"},
        )
        assert resp.status_code == 403


class TestAppendFile:
    def test_append_free_file(self, client: TestClient) -> None:
        resp = client.post(
            "/memory/files/tasks/task-001.md/append",
            json={"content": "\n## New Section\n"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "appended"

    def test_append_secrets_blocked(self, client: TestClient) -> None:
        resp = client.post(
            "/memory/files/tasks/task-001.md/append",
            json={"content": "api_key=abcd1234"},
        )
        assert resp.status_code == 422


class TestProvision:
    def test_provision_project(self, client: TestClient) -> None:
        resp = client.post(
            "/memory/projects/my-new-app/provision",
            json={"slug": "my-new-app", "name": "My New App"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] == "my-new-app"
        assert data["created_count"] == 7

    def test_provision_slug_mismatch(self, client: TestClient) -> None:
        resp = client.post(
            "/memory/projects/wrong-slug/provision",
            json={"slug": "different-slug", "name": "Test"},
        )
        assert resp.status_code == 400


class TestAccessInfo:
    def test_access_info_free(self, client: TestClient) -> None:
        resp = client.get("/memory/access?path=tasks/test.md")
        assert resp.status_code == 200
        assert resp.json()["access_tier"] == "free"

    def test_access_info_approval(self, client: TestClient) -> None:
        resp = client.get("/memory/access?path=current_state.md")
        assert resp.status_code == 200
        assert resp.json()["access_tier"] == "approval_required"

    def test_access_info_forbidden(self, client: TestClient) -> None:
        resp = client.get("/memory/access?path=templates/test.md")
        assert resp.status_code == 200
        assert resp.json()["access_tier"] == "forbidden"


class TestReindexAndSearch:
    def test_reindex_success(self, client: TestClient, monkeypatch) -> None:
        from app.services.memory_indexing_service import MemoryReindexResult

        async def _fake_reindex(self, scope: str, project_slug: str | None = None):
            return MemoryReindexResult(
                scanned_files=3,
                indexed_documents=2,
                skipped_documents=1,
                total_chunks=6,
            )

        monkeypatch.setattr(
            "app.services.memory_indexing_service.MemoryIndexingService.reindex",
            _fake_reindex,
        )

        resp = client.post("/memory/reindex", json={"scope": "all"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["scope"] == "all"
        assert data["scanned_files"] == 3
        assert data["total_chunks"] == 6

    def test_search_success(self, client: TestClient, monkeypatch) -> None:
        from app.services.memory_retrieval_service import RetrievalItem

        async def _fake_search(self, query: str, project_slug=None, limit: int = 8, scope=None):
            return [
                RetrievalItem(
                    path="projects/demo-app/overview.md",
                    title="Demo",
                    scope="project",
                    project_slug="demo-app",
                    heading="Overview",
                    chunk_index=0,
                    content="demo content",
                    score=0.91,
                )
            ]

        monkeypatch.setattr(
            "app.services.memory_retrieval_service.MemoryRetrievalService.search",
            _fake_search,
        )

        resp = client.post(
            "/memory/search",
            json={"query": "demo", "project_slug": "demo-app", "limit": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "demo"
        assert data["total"] == 1
        assert data["items"][0]["path"] == "projects/demo-app/overview.md"
