"""Tests for agent schemas and router structure."""

import pytest
from pydantic import ValidationError

from app.routers.agents import router
from app.schemas.agent import AgentCreate, AgentUpdate


class TestAgentCreateSchema:
    def test_valid_minimal(self):
        data = AgentCreate(
            slug="backend",
            name="Backend Agent",
            role="backend-developer",
            system_prompt="You are a backend developer.",
        )
        assert data.slug == "backend"
        assert data.status == "active"
        assert data.permissions == {}

    def test_rejects_empty_role(self):
        with pytest.raises(ValidationError):
            AgentCreate(
                slug="test",
                name="Test",
                role="",
                system_prompt="prompt",
            )


class TestAgentUpdateSchema:
    def test_partial_permissions_update(self):
        data = AgentUpdate(permissions={"deploy_staging": True})
        assert data.permissions == {"deploy_staging": True}
        assert data.name is None


class TestRouterStructure:
    def test_prefix(self):
        assert router.prefix == "/agents"

    def test_routes_exist(self):
        paths = {r.path for r in router.routes}
        assert "/agents" in paths
        assert "/agents/{agent_id}" in paths
