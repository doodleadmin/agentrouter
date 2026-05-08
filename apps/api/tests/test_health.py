"""Tests for the enhanced /health endpoint with DB and Redis checks."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings


@pytest.fixture
async def client() -> AsyncClient:
    """Minimal async HTTP client — health does its own DB/Redis connections."""
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _make_bad_session_factory():
    """Return a plain callable that produces a session mock raising on execute().

    Must return the mock synchronously (not a coroutine) because the health
    endpoint does ``async with AsyncSessionLocal() as session:`` — the call
    ``AsyncSessionLocal()`` is a regular (non-await) call.
    """
    bad_session = AsyncMock()
    bad_session.__aenter__ = AsyncMock(return_value=bad_session)
    bad_session.__aexit__ = AsyncMock(return_value=False)
    bad_session.execute.side_effect = Exception("connection refused")

    def factory():
        return bad_session

    return factory


def _make_bad_redis_module():
    """Return a mock ``redis.asyncio`` module whose ``from_url`` produces a
    client whose ``ping()`` raises.
    """
    mock_module = AsyncMock()
    bad_redis = AsyncMock()
    bad_redis.__aenter__ = AsyncMock(return_value=bad_redis)
    bad_redis.__aexit__ = AsyncMock(return_value=False)
    bad_redis.ping.side_effect = Exception("connection refused")
    mock_module.from_url = lambda _url: bad_redis
    return mock_module


@pytest.mark.anyio
class TestHealthCheck:
    """GET /health behaviour with dependency checks."""

    async def test_health_ok_shape(self, client: AsyncClient) -> None:
        """Basic health check returns expected top-level and checks fields."""
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ok", "degraded")
        assert data["service"] == "agent-mission-control-api"
        assert data["version"] == settings.APP_VERSION
        assert "timestamp" in data
        assert "checks" in data
        assert data["checks"]["api"] == "ok"
        assert data["checks"]["database"] in ("ok", "error")
        assert data["checks"]["redis"] in ("ok", "error")

    async def test_health_db_failure_returns_degraded(self, client: AsyncClient) -> None:
        """DB failure returns degraded status, not 500."""
        with patch(
            "app.routers.health.AsyncSessionLocal",
            _make_bad_session_factory(),
        ):
            resp = await client.get("/health")

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "degraded"
        assert body["checks"]["database"] == "error"

    async def test_health_redis_failure_returns_degraded(self, client: AsyncClient) -> None:
        """Redis failure returns degraded status, not 500."""
        with patch("app.routers.health.aioredis", _make_bad_redis_module()):
            resp = await client.get("/health")

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "degraded"
        assert body["checks"]["redis"] == "error"

    async def test_health_does_not_expose_secrets(self, client: AsyncClient) -> None:
        """No env values, connection strings, or hostnames in response."""
        resp = await client.get("/health")
        text_lower = resp.text.lower()
        forbidden = [
            "password",
            "postgres://",
            "postgresql://",
            "redis://",
            "token",
            "secret",
            "localhost",
            "127.0.0.1",
        ]
        for word in forbidden:
            assert word not in text_lower, f"Forbidden string '{word}' found in health response"
