"""Tests for POST /telegram/webapp/auth."""

import hashlib
import hmac
import json
from urllib.parse import urlencode

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings


def _build_init_data(payload: dict[str, str], bot_token: str) -> str:
    data_check_string = "\n".join(sorted(f"{k}={v}" for k, v in payload.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    digest = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    signed = dict(payload)
    signed["hash"] = digest
    return urlencode(signed)


@pytest.fixture
async def client() -> AsyncClient:
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_webapp_auth_valid(client: AsyncClient) -> None:
    settings.TELEGRAM_BOT_TOKEN = "unit-test-bot-token"
    user = {"id": 123456, "first_name": "Ivan", "last_name": "Petrov", "username": "ivanp"}
    init_data = _build_init_data(
        {
            "auth_date": "1715000000",
            "query_id": "AAEAAAE",
            "user": json.dumps(user, separators=(",", ":")),
        },
        settings.TELEGRAM_BOT_TOKEN,
    )

    resp = await client.post("/telegram/webapp/auth", json={"initData": init_data})
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == 123456
    assert data["first_name"] == "Ivan"
    assert data["username"] == "ivanp"
    assert data["auth_date"] == 1715000000
    assert "..." in data["hash_summary"]


@pytest.mark.anyio
async def test_webapp_auth_invalid_signature(client: AsyncClient) -> None:
    settings.TELEGRAM_BOT_TOKEN = "unit-test-bot-token"
    init_data = "auth_date=1715000000&user=%7B%22id%22%3A123%7D&hash=bad"
    resp = await client.post("/telegram/webapp/auth", json={"initData": init_data})
    assert resp.status_code == 400
    assert "signature is invalid" in resp.text


@pytest.mark.anyio
async def test_webapp_auth_missing_init_data(client: AsyncClient) -> None:
    resp = await client.post("/telegram/webapp/auth", json={})
    assert resp.status_code == 422
