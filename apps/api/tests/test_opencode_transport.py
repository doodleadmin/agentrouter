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


# BE-07 contract-aligned payload for POST /session/{id}/message
PARTS_PAYLOAD = {"parts": [{"type": "text", "text": "plan"}]}


@pytest.mark.anyio
async def test_send_message_uses_post_session_id_message_endpoint() -> None:
    client = _mk_client_for_post(json_data={"parts": [{"type": "step-finish", "reason": "stop"}]})
    transport = _mk_transport(client)

    data = await transport.send_message("abc", PARTS_PAYLOAD)

    assert data["parts"][0]["type"] == "step-finish"
    assert client.post.call_args[0][0] == "/session/abc/message"


@pytest.mark.anyio
async def test_send_message_contract_aligned_payload_shape() -> None:
    """BE-07: verify transport sends parts-based payload (not legacy message field)."""
    client = _mk_client_for_post(json_data={"parts": [{"type": "step-finish", "reason": "stop"}]})
    transport = _mk_transport(client)

    await transport.send_message("abc", PARTS_PAYLOAD)

    sent_payload = client.post.call_args.kwargs["json"]
    # Must be parts-based, NOT legacy message field
    assert sent_payload == {"parts": [{"type": "text", "text": "plan"}]}
    assert "message" not in sent_payload
    assert "mode" not in sent_payload
    assert "correlation_id" not in sent_payload


@pytest.mark.anyio
async def test_send_message_non_object_response_fails_closed() -> None:
    client = _mk_client_for_post(json_data=[{"type": "step-finish"}])
    transport = _mk_transport(client)

    with pytest.raises(OpenCodeTransportError, match="JSON object"):
        await transport.send_message("abc", PARTS_PAYLOAD)


@pytest.mark.anyio
async def test_send_message_maps_http_errors() -> None:
    client = _mk_client_for_post(status_code=503, json_data={"error": "down"})
    transport = _mk_transport(client)
    with pytest.raises(OpenCodeHTTPError):
        await transport.send_message("abc", PARTS_PAYLOAD)


@pytest.mark.anyio
async def test_send_message_connection_error_maps() -> None:
    client = _mk_client_for_post(side_effect=httpx.ConnectError("refused"))
    transport = _mk_transport(client)
    with pytest.raises(OpenCodeConnectionError):
        await transport.send_message("abc", PARTS_PAYLOAD)


@pytest.mark.anyio
async def test_send_message_timeout_maps() -> None:
    client = _mk_client_for_post(side_effect=httpx.ReadTimeout("timeout"))
    transport = _mk_transport(client)
    with pytest.raises(OpenCodeTimeoutError):
        await transport.send_message("abc", PARTS_PAYLOAD)


# ── BE-08 session payload shape tests ──────────────────────────────────

# BE-08: OpenCode 1.14.33 only accepts `title` for POST /session.
# All other fields are IGNORED. Payload must be minimal.

BE08_SESSION_PAYLOAD = {"title": "Plan task"}

BE08_FORBIDDEN_SESSION_FIELDS = frozenset(
    {"directory", "cwd", "path", "workspace", "mode", "model",
     "capabilities", "restrictions", "projectID", "agent"}
)


@pytest.mark.anyio
async def test_create_session_payload_includes_title() -> None:
    """BE-08: POST /session payload must include `title` field."""
    client = _mk_client_for_post(json_data={"session_id": "s-be08-title"})
    transport = _mk_transport(client)

    sid = await transport.create_session(BE08_SESSION_PAYLOAD)

    assert sid == "s-be08-title"
    sent_json = client.post.call_args.kwargs["json"]
    assert "title" in sent_json
    assert sent_json["title"] == "Plan task"


@pytest.mark.anyio
async def test_create_session_payload_excludes_forbidden_fields() -> None:
    """BE-08: POST /session payload must NOT include directory/cwd/path/
    workspace/mode/model/capabilities/restrictions/projectID/agent."""
    client = _mk_client_for_post(json_data={"session_id": "s-be08-clean"})
    transport = _mk_transport(client)

    await transport.create_session(BE08_SESSION_PAYLOAD)

    sent_json = client.post.call_args.kwargs["json"]
    for forbidden in BE08_FORBIDDEN_SESSION_FIELDS:
        assert forbidden not in sent_json, (
            f"Forbidden field '{forbidden}' found in session payload: {sent_json}"
        )
