"""Tests for the /version endpoint."""

import sys

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings


@pytest.fixture
async def client() -> AsyncClient:
    """Minimal async HTTP client — no DB needed for /version."""
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
class TestVersionEndpoint:
    """GET /version behaviour."""

    async def test_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/version")
        assert resp.status_code == 200

    async def test_returns_json_content_type(self, client: AsyncClient) -> None:
        resp = await client.get("/version")
        assert resp.headers["content-type"] == "application/json"

    async def test_contains_expected_fields(self, client: AsyncClient) -> None:
        resp = await client.get("/version")
        body = resp.json()
        assert "version" in body
        assert "name" in body
        assert "commit_sha" in body
        assert "build_time" in body
        assert "python_version" in body
        assert "debug" in body

    async def test_version_matches_settings(self, client: AsyncClient) -> None:
        resp = await client.get("/version")
        body = resp.json()
        assert body["version"] == settings.APP_VERSION

    async def test_name_matches_settings(self, client: AsyncClient) -> None:
        resp = await client.get("/version")
        body = resp.json()
        assert body["name"] == settings.APP_NAME

    async def test_debug_matches_settings(self, client: AsyncClient) -> None:
        resp = await client.get("/version")
        body = resp.json()
        assert body["debug"] == settings.DEBUG

    async def test_commit_sha_defaults_to_unknown(self, client: AsyncClient) -> None:
        """Without build-time injection, COMMIT_SHA is 'unknown'."""
        resp = await client.get("/version")
        body = resp.json()
        assert body["commit_sha"] == "unknown"

    async def test_build_time_defaults_to_unknown(self, client: AsyncClient) -> None:
        """Without build-time injection, BUILD_TIME is 'unknown'."""
        resp = await client.get("/version")
        body = resp.json()
        assert body["build_time"] == "unknown"

    async def test_python_version_is_valid_semver(self, client: AsyncClient) -> None:
        resp = await client.get("/version")
        body = resp.json()
        parts = body["python_version"].split(".")
        assert len(parts) >= 2  # e.g. "3.12" or "3.12.4"
        assert all(p.isdigit() for p in parts)

    async def test_python_version_matches_runtime(self, client: AsyncClient) -> None:
        resp = await client.get("/version")
        body = resp.json()
        assert body["python_version"] == sys.version.split()[0]
