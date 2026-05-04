"""BE-06 unit tests for RealOpenCodeHttpTransport (mocked httpx)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.config import settings
from app.integrations.opencode.transport import (
    OpenCodeConnectionError,
    OpenCodeHTTPError,
    OpenCodeTimeoutError,
    OpenCodeTransportError,
    RealOpenCodeHttpTransport,
)


def test_default_read_timeout_is_bounded_and_not_none() -> None:
    transport = RealOpenCodeHttpTransport(base_url="http://opencode.local")
    assert transport._read_timeout is not None
    assert transport._read_timeout == float(settings.RUNTIME_SESSION_TIMEOUT_SECONDS)


def _mk_transport(mock_client: MagicMock) -> RealOpenCodeHttpTransport:
    transport = RealOpenCodeHttpTransport(base_url="http://opencode.local")
    transport._build_client = MagicMock(return_value=mock_client)
    return transport


def _mk_client_for_post(*, json_data=None, status_code=200, side_effect=None) -> MagicMock:
    client = MagicMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    if side_effect is not None:
        client.post = AsyncMock(side_effect=side_effect)
        return client

    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data if json_data is not None else {}
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error",
            request=MagicMock(),
            response=MagicMock(status_code=status_code),
        )
    client.post = AsyncMock(return_value=resp)
    return client


@pytest.mark.anyio
async def test_create_session_uses_post_session_endpoint() -> None:
    client = _mk_client_for_post(json_data={"session_id": "s-1"})
    transport = _mk_transport(client)

    sid = await transport.create_session({"mode": "plan_only"})

    assert sid == "s-1"
    assert client.post.call_args[0][0] == "/session"


@pytest.mark.anyio
async def test_create_session_does_not_use_legacy_sessions_endpoint() -> None:
    client = _mk_client_for_post(json_data={"session_id": "s-2"})
    transport = _mk_transport(client)

    await transport.create_session({"mode": "plan_only"})

    called_url = client.post.call_args[0][0]
    assert called_url != "/sessions"


@pytest.mark.anyio
async def test_send_message_uses_post_session_id_message_endpoint() -> None:
    client = _mk_client_for_post(json_data={"parts": [{"kind": "final"}]})
    transport = _mk_transport(client)

    data = await transport.send_message("abc", {"message": "plan"})

    assert data["parts"][0]["kind"] == "final"
    assert client.post.call_args[0][0] == "/session/abc/message"


@pytest.mark.anyio
async def test_send_message_contract_aligned_payload_shape() -> None:
    client = _mk_client_for_post(json_data={"parts": [{"kind": "final"}]})
    transport = _mk_transport(client)

    await transport.send_message(
        "abc",
        {
            "message": "plan",
        },
    )

    sent_payload = client.post.call_args.kwargs["json"]
    assert sent_payload == {"message": "plan"}


@pytest.mark.anyio
async def test_send_message_non_object_response_fails_closed() -> None:
    client = _mk_client_for_post(json_data=[{"kind": "final"}])
    transport = _mk_transport(client)

    with pytest.raises(OpenCodeTransportError, match="JSON object"):
        await transport.send_message("abc", {"message": "plan"})


@pytest.mark.anyio
async def test_send_message_maps_http_errors() -> None:
    client = _mk_client_for_post(status_code=503, json_data={"error": "down"})
    transport = _mk_transport(client)
    with pytest.raises(OpenCodeHTTPError):
        await transport.send_message("abc", {"message": "plan"})


@pytest.mark.anyio
async def test_send_message_connection_error_maps() -> None:
    client = _mk_client_for_post(side_effect=httpx.ConnectError("refused"))
    transport = _mk_transport(client)
    with pytest.raises(OpenCodeConnectionError):
        await transport.send_message("abc", {"message": "plan"})


@pytest.mark.anyio
async def test_send_message_timeout_maps() -> None:
    client = _mk_client_for_post(side_effect=httpx.ReadTimeout("timeout"))
    transport = _mk_transport(client)
    with pytest.raises(OpenCodeTimeoutError):
        await transport.send_message("abc", {"message": "plan"})
