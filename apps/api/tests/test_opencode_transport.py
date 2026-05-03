"""BE-05 unit tests for RealOpenCodeHttpTransport (mocked httpx)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.integrations.opencode.transport import (
    OpenCodeConnectionError,
    OpenCodeHTTPError,
    OpenCodeTimeoutError,
    OpenCodeTransportError,
    RealOpenCodeHttpTransport,
)


# ── Helpers ────────────────────────────────────────────────────────────

def _make_mock_client(
    *,
    post_json: dict | None = None,
    post_status: int = 200,
    post_side_effect: Exception | None = None,
    stream_lines: list[str] | None = None,
    stream_status: int = 200,
    stream_side_effect: Exception | None = None,
) -> tuple[MagicMock, RealOpenCodeHttpTransport]:
    """Build a RealOpenCodeHttpTransport with a mocked _build_client."""
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    # Mock POST
    if post_side_effect:
        mock_client.post = AsyncMock(side_effect=post_side_effect)
    else:
        mock_resp = MagicMock()
        mock_resp.status_code = post_status
        mock_resp.json.return_value = post_json or {}
        mock_resp.raise_for_status = MagicMock()
        if post_status >= 400:
            mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                "error",
                request=MagicMock(),
                response=MagicMock(status_code=post_status),
            )
        mock_client.post = AsyncMock(return_value=mock_resp)

    # Mock stream
    mock_stream_resp = MagicMock()
    mock_stream_resp.status_code = stream_status
    mock_stream_resp.raise_for_status = MagicMock()
    if stream_status >= 400:
        mock_stream_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error",
            request=MagicMock(),
            response=MagicMock(status_code=stream_status),
        )
    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_stream_resp)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=None)

    if stream_side_effect:
        mock_client.stream = MagicMock(side_effect=stream_side_effect)
    elif stream_lines is not None:
        mock_stream_resp.aiter_lines = MagicMock(return_value=_async_iter(stream_lines))
        mock_client.stream = MagicMock(return_value=mock_stream_ctx)
    else:
        # Default empty stream
        mock_stream_resp.aiter_lines = MagicMock(return_value=_async_iter([]))
        mock_client.stream = MagicMock(return_value=mock_stream_ctx)

    transport = RealOpenCodeHttpTransport(
        base_url="http://opencode.local",
        connect_timeout=1.0,
        read_timeout=1.0,
        write_timeout=1.0,
        session_timeout=5.0,
        idle_timeout=2.0,
    )
    transport._build_client = MagicMock(return_value=mock_client)
    return mock_client, transport


async def _async_iter(items: list[str]):
    for item in items:
        yield item


# ── T1: create_session success ─────────────────────────────────────────

@pytest.mark.anyio
async def test_create_session_returns_session_id() -> None:
    _, transport = _make_mock_client(
        post_json={"session_id": "abc-123"},
        post_status=200,
    )
    sid = await transport.create_session({"mode": "plan_only"})
    assert sid == "abc-123"


@pytest.mark.anyio
async def test_create_session_uses_id_field_as_fallback() -> None:
    _, transport = _make_mock_client(
        post_json={"id": "fallback-id"},
        post_status=200,
    )
    sid = await transport.create_session({"mode": "plan_only"})
    assert sid == "fallback-id"


# ── T2: create_session HTTP error ──────────────────────────────────────

@pytest.mark.anyio
async def test_create_session_http_500_raises_http_error() -> None:
    _, transport = _make_mock_client(
        post_status=500,
        post_json={"error": "internal"},
    )
    with pytest.raises(OpenCodeHTTPError):
        await transport.create_session({"mode": "plan_only"})


@pytest.mark.anyio
async def test_create_session_missing_session_id_raises_transport_error() -> None:
    _, transport = _make_mock_client(
        post_status=200,
        post_json={"other": "data"},
    )
    with pytest.raises(OpenCodeTransportError, match="missing session_id"):
        await transport.create_session({"mode": "plan_only"})


# ── T3: create_session connection error ────────────────────────────────

@pytest.mark.anyio
async def test_create_session_connect_error_raises_connection_error() -> None:
    _, transport = _make_mock_client(
        post_side_effect=httpx.ConnectError("refused"),
    )
    with pytest.raises(OpenCodeConnectionError):
        await transport.create_session({"mode": "plan_only"})


@pytest.mark.anyio
async def test_create_session_read_timeout_raises_timeout_error() -> None:
    _, transport = _make_mock_client(
        post_side_effect=httpx.ReadTimeout("timeout"),
    )
    with pytest.raises(OpenCodeTimeoutError):
        await transport.create_session({"mode": "plan_only"})


# ── T5: stream_events success ──────────────────────────────────────────

@pytest.mark.anyio
async def test_stream_events_yields_parsed_events() -> None:
    lines = [
        "data: " + json.dumps({"type": "plan.delta", "event_id": "1", "text": "hello"}),
        "",
        "data: " + json.dumps({"type": "plan.final", "event_id": "2"}),
        "",
    ]
    _, transport = _make_mock_client(stream_lines=lines)
    events = [e async for e in transport.stream_events("sess-1")]
    assert len(events) == 2
    assert events[0]["type"] == "plan.delta"
    assert events[1]["type"] == "plan.final"


@pytest.mark.anyio
async def test_stream_events_multiline_data() -> None:
    lines = [
        "data: {\"type\": \"plan.delta\",",
        "data:  \"event_id\": \"1\"}",
        "",
    ]
    _, transport = _make_mock_client(stream_lines=lines)
    events = [e async for e in transport.stream_events("sess-1")]
    assert len(events) == 1
    assert events[0]["type"] == "plan.delta"


@pytest.mark.anyio
async def test_stream_events_non_json_data_parsed_as_plan_delta() -> None:
    lines = [
        "data: just plain text",
        "",
    ]
    _, transport = _make_mock_client(stream_lines=lines)
    events = [e async for e in transport.stream_events("sess-1")]
    assert len(events) == 1
    assert events[0]["type"] == "plan.delta"
    assert events[0]["text"] == "just plain text"


@pytest.mark.anyio
async def test_stream_events_ignores_non_data_lines() -> None:
    lines = [
        "event: message",
        "id: 42",
        "data: " + json.dumps({"type": "plan.delta", "text": "x"}),
        "",
    ]
    _, transport = _make_mock_client(stream_lines=lines)
    events = [e async for e in transport.stream_events("sess-1")]
    assert len(events) == 1
    assert events[0]["type"] == "plan.delta"


@pytest.mark.anyio
async def test_stream_events_empty_buffer_yields_nothing() -> None:
    lines = [
        "",
        "   ",
        "",
    ]
    _, transport = _make_mock_client(stream_lines=lines)
    events = [e async for e in transport.stream_events("sess-1")]
    assert len(events) == 0


# ── T6: stream_events session total timeout ────────────────────────────

@pytest.mark.anyio
async def test_stream_events_session_timeout_raises_timeout_error() -> None:
    """Session total timeout of 5s, but stream just sits."""
    # Produce many empty lines that don't yield events (delaying progress)
    lines = ["data: " + json.dumps({"type": "plan.delta", "text": "x"}), ""]
    _, transport = _make_mock_client(stream_lines=lines)

    # Force session timeout by patching time.monotonic
    call_count = [0]

    def _fake_monotonic():
        call_count[0] += 1
        # First call = start_time (0), then jump to 100
        if call_count[0] == 1:
            return 0.0
        return 100.0  # way past 5s session timeout

    with patch("app.integrations.opencode.transport.time.monotonic", _fake_monotonic):
        with pytest.raises(OpenCodeTimeoutError, match="exceeded total timeout"):
            _ = [e async for e in transport.stream_events("sess-1")]


# ── T7: stream_events idle timeout ─────────────────────────────────────

@pytest.mark.anyio
async def test_stream_events_idle_timeout_raises_timeout_error() -> None:
    lines = [
        "data: " + json.dumps({"type": "plan.delta", "text": "x"}),
        "",
        "data: " + json.dumps({"type": "plan.delta", "text": "y"}),
        "",
    ]
    # transport with large session timeout (1000s), small idle timeout (2s)
    transport = RealOpenCodeHttpTransport(
        base_url="http://opencode.local",
        session_timeout=1000.0,
        idle_timeout=2.0,
    )
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_stream_resp = MagicMock()
    mock_stream_resp.status_code = 200
    mock_stream_resp.raise_for_status = MagicMock()
    mock_stream_resp.aiter_lines = MagicMock(return_value=_async_iter(lines))
    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_stream_resp)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=None)
    mock_client.stream = MagicMock(return_value=mock_stream_ctx)
    transport._build_client = MagicMock(return_value=mock_client)

    call_count = [0]

    def _fake_monotonic():
        call_count[0] += 1
        # Increment slowly: 0, 1, 2, ... then after first event, stall at 10
        if call_count[0] <= 4:
            return float(call_count[0] - 1)
        return 10.0  # idle gap is > 2s, but total is 10s < 1000s

    with patch("app.integrations.opencode.transport.time.monotonic", _fake_monotonic):
        with pytest.raises(OpenCodeTimeoutError, match="idle timeout"):
            _ = [e async for e in transport.stream_events("sess-1")]


# ── T8: stream_events connection error ─────────────────────────────────

@pytest.mark.anyio
async def test_stream_events_connect_error_raises_connection_error() -> None:
    _, transport = _make_mock_client(
        stream_side_effect=httpx.ConnectError("refused"),
    )
    with pytest.raises(OpenCodeConnectionError):
        _ = [e async for e in transport.stream_events("sess-1")]


@pytest.mark.anyio
async def test_stream_events_read_timeout_raises_timeout_error() -> None:
    _, transport = _make_mock_client(
        stream_side_effect=httpx.ReadTimeout("timeout"),
    )
    with pytest.raises(OpenCodeTimeoutError):
        _ = [e async for e in transport.stream_events("sess-1")]


@pytest.mark.anyio
async def test_stream_events_http_status_error_raises_http_error() -> None:
    _, transport = _make_mock_client(stream_status=503)
    with pytest.raises(OpenCodeHTTPError):
        _ = [e async for e in transport.stream_events("sess-1")]


# ── Redaction in transport ─────────────────────────────────────────────

@pytest.mark.anyio
async def test_create_session_redacts_payload_before_send() -> None:
    mock_client, transport = _make_mock_client(
        post_json={"session_id": "s1"},
        post_status=200,
    )
    payload = {"api_key": "super-secret-123", "text": "hello"}
    await transport.create_session(payload)

    call_args = mock_client.post.call_args
    sent_json = call_args[1]["json"]
    assert sent_json["api_key"] == "[REDACTED]"
    assert sent_json["text"] == "hello"


@pytest.mark.anyio
async def test_create_session_redacts_error_messages() -> None:
    _, transport = _make_mock_client(
        post_side_effect=httpx.ConnectError("token=abc123 leaked"),
    )
    with pytest.raises(OpenCodeConnectionError) as exc_info:
        await transport.create_session({"mode": "plan_only"})
    msg = str(exc_info.value)
    assert "abc123" not in msg.lower()
    assert "redacted" in msg.lower() or "[REDACTED]" in msg


# ── URL redaction ──────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_url_params_are_redacted() -> None:
    transport = RealOpenCodeHttpTransport(base_url="http://opencode.local")
    url = "http://opencode.local?token=abc123&password=s3cret"
    redacted = transport._redact_url(url)
    assert "abc123" not in redacted
    assert "s3cret" not in redacted


# ── BE-05 M-2: SSE non-JSON chunk size limit ───────────────────────────


@pytest.mark.anyio
async def test_sse_non_json_chunk_under_limit_not_truncated() -> None:
    """Non-JSON SSE data under 64KB limit should pass through unchanged."""
    small_text = "just plain text"
    event = RealOpenCodeHttpTransport._parse_sse_event(f"data: {small_text}\n")
    assert event is not None
    assert event["type"] == "plan.delta"
    assert event["text"] == small_text
    assert "_sse_chunk_truncated" not in event


@pytest.mark.anyio
async def test_sse_non_json_chunk_over_64kb_truncated_safely() -> None:
    """BE-05 M-2: Non-JSON SSE chunk exceeding 64KB must be truncated with metadata."""
    # Build a non-JSON data string that exceeds 64KB
    oversize = "X" * (65 * 1024)  # 65KB, over 64KB limit
    # Simulate SSE buffer with one giant data line
    buffer = f"data: {oversize}\n"
    event = RealOpenCodeHttpTransport._parse_sse_event(buffer)

    assert event is not None
    assert event["type"] == "plan.delta"
    assert event["_sse_chunk_truncated"] is True

    # Text should be truncated to at most 64KB
    text_bytes = len(event["text"].encode("utf-8"))
    assert text_bytes <= RealOpenCodeHttpTransport._SSE_CHUNK_SIZE_LIMIT
    assert text_bytes < len(oversize.encode("utf-8"))


@pytest.mark.anyio
async def test_sse_non_json_chunk_exactly_at_limit_not_truncated() -> None:
    """Non-JSON SSE data exactly at 64KB should not be truncated."""
    # Build data exactly at the limit
    exactly_limit = "A" * RealOpenCodeHttpTransport._SSE_CHUNK_SIZE_LIMIT
    buffer = f"data: {exactly_limit}\n"
    event = RealOpenCodeHttpTransport._parse_sse_event(buffer)

    assert event is not None
    assert event["type"] == "plan.delta"
    assert "_sse_chunk_truncated" not in event
    assert len(event["text"].encode("utf-8")) == RealOpenCodeHttpTransport._SSE_CHUNK_SIZE_LIMIT


@pytest.mark.anyio
async def test_sse_json_chunk_over_64kb_not_truncated() -> None:
    """JSON SSE data over 64KB should NOT be truncated — limit only applies to non-JSON."""
    # Build a valid JSON object that is over 64KB
    big_text = "Y" * (65 * 1024)
    json_str = json.dumps({"type": "plan.delta", "event_id": "1", "text": big_text})
    buffer = f"data: {json_str}\n"
    event = RealOpenCodeHttpTransport._parse_sse_event(buffer)

    assert event is not None
    assert event["type"] == "plan.delta"
    assert event["text"] == big_text
    assert "_sse_chunk_truncated" not in event
