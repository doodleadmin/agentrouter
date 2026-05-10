"""Tests for POST /telegram/webapp/auth — signature, freshness, session token."""

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings


def _build_init_data(
    payload: dict[str, str],
    bot_token: str,
    *,
    auth_date: int | None = None,
) -> str:
    """Build signed initData with optional auth_date override."""
    final = dict(payload)
    if auth_date is not None:
        final["auth_date"] = str(auth_date)
    data_check_string = "\n".join(sorted(f"{k}={v}" for k, v in final.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    digest = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    signed = dict(final)
    signed["hash"] = digest
    return urlencode(signed)


@pytest.fixture
async def client() -> AsyncClient:
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── existing tests (kept, updated for session_token) ────────────────────


@pytest.mark.anyio
async def test_webapp_auth_valid(client: AsyncClient) -> None:
    settings.TELEGRAM_BOT_TOKEN = "unit-test-bot-token"
    now = int(time.time())
    user = {"id": 123456, "first_name": "Ivan", "last_name": "Petrov", "username": "ivanp"}
    init_data = _build_init_data(
        {
            "query_id": "AAEAAAE",
            "user": json.dumps(user, separators=(",", ":")),
        },
        settings.TELEGRAM_BOT_TOKEN,
        auth_date=now,
    )

    resp = await client.post("/telegram/webapp/auth", json={"initData": init_data})
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == 123456
    assert data["first_name"] == "Ivan"
    assert data["username"] == "ivanp"
    assert data["auth_date"] == now
    assert "..." in data["hash_summary"]
    assert len(data["session_token"]) == 32


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


# ── NEW: auth hardening tests ─────────────────────────────────────────


@pytest.mark.anyio
async def test_webapp_auth_stale_init_data_rejected(client: AsyncClient) -> None:
    """initData older than 300 seconds must be rejected."""
    settings.TELEGRAM_BOT_TOKEN = "unit-test-bot-token"
    stale_auth_date = int(time.time()) - 600  # 10 minutes ago
    user = {"id": 111, "first_name": "Stale"}
    init_data = _build_init_data(
        {"user": json.dumps(user, separators=(",", ":"))},
        settings.TELEGRAM_BOT_TOKEN,
        auth_date=stale_auth_date,
    )

    resp = await client.post("/telegram/webapp/auth", json={"initData": init_data})
    assert resp.status_code == 400
    assert "too old" in resp.text


@pytest.mark.anyio
async def test_webapp_auth_future_auth_date_rejected(client: AsyncClient) -> None:
    """initData with auth_date in the future must be rejected."""
    settings.TELEGRAM_BOT_TOKEN = "unit-test-bot-token"
    future_auth_date = int(time.time()) + 600
    user = {"id": 222, "first_name": "Future"}
    init_data = _build_init_data(
        {"user": json.dumps(user, separators=(",", ":"))},
        settings.TELEGRAM_BOT_TOKEN,
        auth_date=future_auth_date,
    )

    resp = await client.post("/telegram/webapp/auth", json={"initData": init_data})
    assert resp.status_code == 400
    assert "future" in resp.text.lower()


@pytest.mark.anyio
async def test_webapp_auth_tampered_user_payload_rejected(client: AsyncClient) -> None:
    """Modifying user payload after signing must break the hash."""
    settings.TELEGRAM_BOT_TOKEN = "unit-test-bot-token"
    now = int(time.time())
    user = {"id": 333, "first_name": "Honest"}
    init_data = _build_init_data(
        {"user": json.dumps(user, separators=(",", ":"))},
        settings.TELEGRAM_BOT_TOKEN,
        auth_date=now,
    )
    # Tamper: replace user name in the query string
    tampered = init_data.replace("Honest", "Evil")

    resp = await client.post("/telegram/webapp/auth", json={"initData": tampered})
    assert resp.status_code == 400
    assert "signature is invalid" in resp.text


@pytest.mark.anyio
async def test_webapp_auth_missing_hash_rejected(client: AsyncClient) -> None:
    """initData without hash must be rejected."""
    settings.TELEGRAM_BOT_TOKEN = "unit-test-bot-token"
    resp = await client.post(
        "/telegram/webapp/auth",
        json={"initData": "auth_date=1715000000&user=%7B%22id%22%3A1%7D"},
    )
    assert resp.status_code == 400
    assert "hash" in resp.text.lower()


@pytest.mark.anyio
async def test_webapp_auth_missing_user_rejected(client: AsyncClient) -> None:
    """initData without user payload must be rejected (even with valid hash)."""
    settings.TELEGRAM_BOT_TOKEN = "unit-test-bot-token"
    now = int(time.time())
    init_data = _build_init_data(
        {"query_id": "AAEAAAE"},
        settings.TELEGRAM_BOT_TOKEN,
        auth_date=now,
    )
    # Remove user field but keep hash — hash will still be valid
    # but user is required
    resp = await client.post("/telegram/webapp/auth", json={"initData": init_data})
    assert resp.status_code == 400
    assert "user" in resp.text.lower()


@pytest.mark.anyio
async def test_webapp_auth_malformed_user_json_rejected(client: AsyncClient) -> None:
    """initData with non-JSON user payload must be rejected."""
    settings.TELEGRAM_BOT_TOKEN = "unit-test-bot-token"
    now = int(time.time())
    # Manually build with malformed user JSON
    pairs = {
        "auth_date": str(now),
        "query_id": "AAEAAAE",
        "user": "not-json",
    }
    data_check_string = "\n".join(sorted(f"{k}={v}" for k, v in pairs.items()))
    secret_key = hmac.new(b"WebAppData", settings.TELEGRAM_BOT_TOKEN.encode("utf-8"), hashlib.sha256).digest()
    digest = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    pairs["hash"] = digest
    init_data = urlencode(pairs)

    resp = await client.post("/telegram/webapp/auth", json={"initData": init_data})
    assert resp.status_code == 400
    assert "malformed" in resp.text.lower()


@pytest.mark.anyio
async def test_webapp_auth_no_bot_token_rejected(client: AsyncClient) -> None:
    """Missing bot token must result in 400."""
    settings.TELEGRAM_BOT_TOKEN = ""
    now = int(time.time())
    user = {"id": 444, "first_name": "Tokenless"}
    init_data = _build_init_data(
        {"user": json.dumps(user, separators=(",", ":"))},
        "any-token",
        auth_date=now,
    )

    resp = await client.post("/telegram/webapp/auth", json={"initData": init_data})
    assert resp.status_code == 400
    assert "token" in resp.text.lower()


@pytest.mark.anyio
async def test_webapp_auth_fresh_within_boundary(client: AsyncClient) -> None:
    """initData exactly at max age boundary (299s) must pass."""
    settings.TELEGRAM_BOT_TOKEN = "unit-test-bot-token"
    boundary_auth_date = int(time.time()) - 299
    user = {"id": 555, "first_name": "Boundary"}
    init_data = _build_init_data(
        {"user": json.dumps(user, separators=(",", ":"))},
        settings.TELEGRAM_BOT_TOKEN,
        auth_date=boundary_auth_date,
    )

    resp = await client.post("/telegram/webapp/auth", json={"initData": init_data})
    assert resp.status_code == 200
    assert resp.json()["session_token"]


@pytest.mark.anyio
async def test_webapp_auth_session_token_is_deterministic(client: AsyncClient) -> None:
    """Same initData must always produce the same session_token."""
    settings.TELEGRAM_BOT_TOKEN = "unit-test-bot-token"
    now = int(time.time())
    user = {"id": 666, "first_name": "Deterministic"}
    init_data = _build_init_data(
        {"user": json.dumps(user, separators=(",", ":"))},
        settings.TELEGRAM_BOT_TOKEN,
        auth_date=now,
    )

    resp1 = await client.post("/telegram/webapp/auth", json={"initData": init_data})
    resp2 = await client.post("/telegram/webapp/auth", json={"initData": init_data})
    assert resp1.json()["session_token"] == resp2.json()["session_token"]
