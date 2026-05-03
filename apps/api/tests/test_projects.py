"""Tests for project schemas and router structure."""

import pytest
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
