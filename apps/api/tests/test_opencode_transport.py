"""BE-06 / BE-12 unit tests for RealOpenCodeHttpTransport (mocked httpx).

BE-12 (2026-05-05): send_message read-timeout alignment with OpenCode SDK.
send_message now uses local httpx.AsyncClient with read=None instead of
the bounded _build_client(). Tests updated to patch httpx.AsyncClient.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

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
    """Create transport with mocked _build_client (for create_session tests)."""
    transport = RealOpenCodeHttpTransport(base_url="http://opencode.local")
    transport._build_client = MagicMock(return_value=mock_client)
    return transport


def _mk_transport_for_message() -> RealOpenCodeHttpTransport:
    """Create transport WITHOUT mocking _build_client (for send_message tests).

    send_message() creates its own httpx.AsyncClient (read=None), so
    patch("httpx.AsyncClient") must be used in individual tests.
    """
    return RealOpenCodeHttpTransport(base_url="http://opencode.local")


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


# BE-07 / BE-12 contract-aligned payload for POST /session/{id}/message
PARTS_PAYLOAD = {"parts": [{"type": "text", "text": "plan"}]}


@pytest.mark.anyio
@patch("httpx.AsyncClient")
async def test_send_message_uses_post_session_id_message_endpoint(
    mock_async_client_cls: MagicMock,
) -> None:
    client = _mk_client_for_post(
        json_data={"parts": [{"type": "step-finish", "reason": "stop"}]}
    )
    mock_async_client_cls.return_value = client
    transport = _mk_transport_for_message()

    data = await transport.send_message("abc", PARTS_PAYLOAD)

    assert data["parts"][0]["type"] == "step-finish"
    assert client.post.call_args[0][0] == "/session/abc/message"


@pytest.mark.anyio
@patch("httpx.AsyncClient")
async def test_send_message_contract_aligned_payload_shape(
    mock_async_client_cls: MagicMock,
) -> None:
    """BE-07: verify transport sends parts-based payload (not legacy message field)."""
    client = _mk_client_for_post(
        json_data={"parts": [{"type": "step-finish", "reason": "stop"}]}
    )
    mock_async_client_cls.return_value = client
    transport = _mk_transport_for_message()

    await transport.send_message("abc", PARTS_PAYLOAD)

    sent_payload = client.post.call_args.kwargs["json"]
    # Must be parts-based, NOT legacy message field
    assert sent_payload == {"parts": [{"type": "text", "text": "plan"}]}
    assert "message" not in sent_payload
    assert "mode" not in sent_payload
    assert "correlation_id" not in sent_payload


@pytest.mark.anyio
@patch("httpx.AsyncClient")
async def test_send_message_non_object_response_fails_closed(
    mock_async_client_cls: MagicMock,
) -> None:
    client = _mk_client_for_post(json_data=[{"type": "step-finish"}])
    mock_async_client_cls.return_value = client
    transport = _mk_transport_for_message()

    with pytest.raises(OpenCodeTransportError, match="JSON object"):
        await transport.send_message("abc", PARTS_PAYLOAD)


@pytest.mark.anyio
@patch("httpx.AsyncClient")
async def test_send_message_maps_http_errors(
    mock_async_client_cls: MagicMock,
) -> None:
    client = _mk_client_for_post(status_code=503, json_data={"error": "down"})
    mock_async_client_cls.return_value = client
    transport = _mk_transport_for_message()
    with pytest.raises(OpenCodeHTTPError):
        await transport.send_message("abc", PARTS_PAYLOAD)


@pytest.mark.anyio
@patch("httpx.AsyncClient")
async def test_send_message_connection_error_maps(
    mock_async_client_cls: MagicMock,
) -> None:
    client = _mk_client_for_post(side_effect=httpx.ConnectError("refused"))
    mock_async_client_cls.return_value = client
    transport = _mk_transport_for_message()
    with pytest.raises(OpenCodeConnectionError):
        await transport.send_message("abc", PARTS_PAYLOAD)


@pytest.mark.anyio
@patch("httpx.AsyncClient")
async def test_send_message_timeout_maps(
    mock_async_client_cls: MagicMock,
) -> None:
    client = _mk_client_for_post(side_effect=httpx.ReadTimeout("timeout"))
    mock_async_client_cls.return_value = client
    transport = _mk_transport_for_message()
    with pytest.raises(OpenCodeTimeoutError):
        await transport.send_message("abc", PARTS_PAYLOAD)


@pytest.mark.anyio
@patch("httpx.AsyncClient")
async def test_send_message_read_error_maps(
    mock_async_client_cls: MagicMock,
) -> None:
    """BE-12 P2: httpx.ReadError (connection closed mid-response) must
    map to OpenCodeTimeoutError for proper retry/handling.

    When the OpenCode server closes the connection during long inference,
    httpx raises ReadError (NOT ReadTimeout). This must not escape as an
    unhandled exception — it must be caught and mapped to OpenCodeTimeoutError
    so the retry loop in OpenCodeHttpPlanClient can handle it.
    """
    client = _mk_client_for_post(side_effect=httpx.ReadError("connection closed"))
    mock_async_client_cls.return_value = client
    transport = _mk_transport_for_message()
    with pytest.raises(OpenCodeTimeoutError):
        await transport.send_message("abc", PARTS_PAYLOAD)


# ── BE-12 send_message read-timeout alignment tests ──────────────────


@pytest.mark.anyio
@patch("httpx.AsyncClient")
async def test_be12_send_message_uses_read_none_timeout(
    mock_async_client_cls: MagicMock,
) -> None:
    """BE-12: send_message creates httpx.AsyncClient with read=None timeout.

    The OpenCode SDK sets req.timeout=false for POST /session/{id}/message
    because model inference can exceed a fixed read timeout. AMC must align:
    read=None, client-side session/idle timeout provides the safety net.
    """
    client = _mk_client_for_post(
        json_data={"parts": [{"type": "text", "text": "ok"}, {"type": "step-finish", "reason": "stop"}]}
    )
    mock_async_client_cls.return_value = client
    transport = _mk_transport_for_message()

    await transport.send_message("test-id", PARTS_PAYLOAD)

    # Verify httpx.AsyncClient was called with timeout having read=None
    mock_async_client_cls.assert_called_once()
    call_kwargs = mock_async_client_cls.call_args.kwargs
    assert "timeout" in call_kwargs, "AsyncClient must receive timeout param"
    timeout_obj = call_kwargs["timeout"]
    assert isinstance(timeout_obj, httpx.Timeout)
    assert timeout_obj.read is None, (
        f"read timeout must be None (unbounded) for OpenCode SDK alignment, "
        f"got {timeout_obj.read!r}"
    )
    assert timeout_obj.connect is not None, "connect timeout must remain bounded"
    assert timeout_obj.write is not None, "write timeout must remain bounded"


@pytest.mark.anyio
@patch("httpx.AsyncClient")
async def test_be12_send_message_uses_correct_endpoint(
    mock_async_client_cls: MagicMock,
) -> None:
    """BE-12: send_message uses POST /session/{id}/message (correct SDK endpoint)."""
    client = _mk_client_for_post(
        json_data={"parts": [{"type": "step-finish", "reason": "stop"}]}
    )
    mock_async_client_cls.return_value = client
    transport = _mk_transport_for_message()

    await transport.send_message("test-id-789", PARTS_PAYLOAD)

    called_url = client.post.call_args[0][0]
    assert called_url == "/session/test-id-789/message"
    assert "/prompt" not in called_url, (
        "Must use /session/{id}/message, not /prompt or any other endpoint"
    )


@pytest.mark.anyio
@patch("httpx.AsyncClient")
async def test_be12_send_message_base_url_preserved(
    mock_async_client_cls: MagicMock,
) -> None:
    """BE-12: send_message passes correct base_url to AsyncClient."""
    client = _mk_client_for_post(
        json_data={"parts": [{"type": "text", "text": "ok"}, {"type": "step-finish", "reason": "stop"}]}
    )
    mock_async_client_cls.return_value = client
    transport = RealOpenCodeHttpTransport(base_url="http://opencode.local:4096")

    await transport.send_message("test-id", PARTS_PAYLOAD)

    call_kwargs = mock_async_client_cls.call_args.kwargs
    assert call_kwargs["base_url"] == "http://opencode.local:4096"


def test_be12_create_session_still_uses_bounded_read_timeout() -> None:
    """BE-12: create_session must remain bounded (normal read_timeout).

    Only send_message gets read=None. create_session uses _build_client()
    which has the configured session_timeout as read_timeout.
    """
    transport = RealOpenCodeHttpTransport(base_url="http://opencode.local")
    # Verify _read_timeout is still bounded for create_session path
    assert transport._read_timeout is not None
    assert transport._read_timeout == float(settings.RUNTIME_SESSION_TIMEOUT_SECONDS)


def test_be12_build_client_not_affected() -> None:
    """BE-12: _build_client() is NOT changed — remains bounded for create_session."""
    transport = RealOpenCodeHttpTransport(base_url="http://opencode.local")
    timeout = transport._build_timeout()
    assert timeout.read is not None, (
        "_build_timeout must remain bounded; only send_message overrides locally"
    )
    assert timeout.read == float(settings.RUNTIME_SESSION_TIMEOUT_SECONDS)


def test_be12_build_timeout_all_fields_bounded() -> None:
    """BE-12 P3: verify _build_timeout() returns httpx.Timeout with all
    bounds intact (connect, read, write, pool are not None).

    Only send_message() overrides read=None for SDK alignment.
    The default _build_timeout() (used by create_session via _build_client())
    must keep every timeout field bounded to prevent hanging API workers.
    """
    transport = RealOpenCodeHttpTransport(base_url="http://opencode.local")
    timeout = transport._build_timeout()
    assert isinstance(timeout, httpx.Timeout), (
        f"_build_timeout must return httpx.Timeout, got {type(timeout)}"
    )
    assert timeout.connect is not None, "connect timeout must be bounded"
    assert timeout.read is not None, "read timeout must be bounded (send_message overrides locally)"
    assert timeout.write is not None, "write timeout must be bounded"
    assert timeout.pool is not None, "pool timeout must be bounded"


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
