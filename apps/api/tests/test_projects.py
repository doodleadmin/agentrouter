"""Tests for project schemas and router structure."""

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.routers.projects import router
from app.schemas.project import ProjectCreate, ProjectUpdate


class TestProjectCreateSchema:
    """Validate ProjectCreate input constraints."""

    def test_valid_minimal(self):
        data = ProjectCreate(
            slug="test",
            name="Test Project",
            repo_path="/opt/test",
            memory_path="/opt/mem/test",
        )
        assert data.slug == "test"
        assert data.default_branch == "main"
        assert data.status == "active"
        assert data.stack == {}

    def test_rejects_empty_slug(self):
        with pytest.raises(ValidationError):
            ProjectCreate(
                slug="",
                name="Test",
                repo_path="/opt/test",
                memory_path="/opt/mem/test",
            )

    def test_rejects_missing_required(self):
        with pytest.raises(ValidationError):
            ProjectCreate(slug="test")  # type: ignore[call-arg]


class TestProjectUpdateSchema:
    """Partial updates only supply changed fields."""

    def test_partial_name_only(self):
        data = ProjectUpdate(name="New Name")
        assert data.name == "New Name"
        assert data.repo_path is None


class TestRouterStructure:
    """Minimal router config checks."""

    def test_prefix(self):
        assert router.prefix == "/projects"

    def test_tags(self):
        assert router.tags == ["projects"]

    def test_routes_exist(self):
        paths = {r.path for r in router.routes}
        expected = {
            "/projects",
            "/projects/{project_id}",
        }
        assert expected.issubset(paths)


@pytest.mark.anyio
async def test_create_project_persists_for_followup_get(async_client: AsyncClient) -> None:
    create = await async_client.post(
        "/projects",
        json={
            "slug": "persist-project",
            "name": "Persist Project",
            "repo_path": "apps/api",
            "memory_path": ".ai_memory/projects/persist-project",
        },
    )
    assert create.status_code == 201

    listed = await async_client.get("/projects")
    assert listed.status_code == 200
    slugs = [p["slug"] for p in listed.json()]
    assert "persist-project" in slugs
