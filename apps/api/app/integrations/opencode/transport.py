"""RealOpenCodeHttpTransport — HTTP/SSE transport to OpenCode server via httpx."""

from __future__ import annotations

import json
import time
from typing import Any, AsyncIterator

import httpx

from app.config import settings
from app.policy.runtime_guardrails import redact_payload, redact_text


class OpenCodeTransportError(Exception):
    """Transport-level error."""


class OpenCodeConnectionError(OpenCodeTransportError):
    """Failed to connect to OpenCode server."""


class OpenCodeTimeoutError(OpenCodeTransportError):
    """Request to OpenCode server timed out."""


class OpenCodeHTTPError(OpenCodeTransportError):
    """OpenCode server returned HTTP error."""


class RealOpenCodeHttpTransport:
    """Production HTTP/SSE transport to a real OpenCode server.

    Implements OpenCodeTransportProtocol (create_session + stream_events).
    Uses httpx.AsyncClient with configurable timeouts. Handles connection
    errors, HTTP status errors, and read timeouts with domain exceptions.
    Applies redaction to URL params and error messages that may contain secrets.
    """

    _SSE_CHUNK_SIZE_LIMIT: int = 64 * 1024  # 64 KB per-chunk limit for non-JSON SSE data

    def __init__(
        self,
        *,
        base_url: str | None = None,
        connect_timeout: float = 10.0,
        read_timeout: float | None = None,
        write_timeout: float = 10.0,
        session_timeout: float | None = None,
        idle_timeout: float | None = None,
    ) -> None:
        self._base_url = (base_url or settings.OPENCODE_SERVER_URL).rstrip("/")
        self._connect_timeout = connect_timeout
        self._read_timeout = read_timeout
        self._write_timeout = write_timeout
        self._session_timeout = session_timeout or float(settings.RUNTIME_SESSION_TIMEOUT_SECONDS)
        self._idle_timeout = idle_timeout or float(settings.RUNTIME_IDLE_TIMEOUT_SECONDS)

    def _build_timeout(self) -> httpx.Timeout:
        return httpx.Timeout(
            connect=self._connect_timeout,
            read=self._read_timeout,
            write=self._write_timeout,
            pool=self._connect_timeout,
        )

    def _build_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._build_timeout(),
        )

    @staticmethod
    def _redact_url(url: str) -> str:
        return redact_text(url)

    async def create_session(self, payload: dict[str, Any]) -> str:
        """POST /sessions — create a new OpenCode session, return session_id."""
        safe_payload = redact_payload(payload)
        try:
            async with self._build_client() as client:
                resp = await client.post("/sessions", json=safe_payload)
                resp.raise_for_status()
                data = resp.json()
                session_id = data.get("session_id") or data.get("id")
                if not session_id:
                    raise OpenCodeTransportError(
                        "create_session response missing session_id"
                    )
                return str(session_id)
        except httpx.ConnectError as exc:
            raise OpenCodeConnectionError(
                f"Failed to connect to OpenCode: {redact_text(str(exc))}"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise OpenCodeHTTPError(
                f"OpenCode HTTP {exc.response.status_code}: "
                f"{redact_text(str(exc))}"
            ) from exc
        except httpx.ReadTimeout as exc:
            raise OpenCodeTimeoutError(
                f"OpenCode session creation timed out: {redact_text(str(exc))}"
            ) from exc

    async def stream_events(self, session_id: str) -> AsyncIterator[dict[str, Any]]:
        """GET /sessions/{id}/events — SSE stream, yield parsed event dicts.

        Enforces session total timeout and idle timeout during iteration.
        """
        url = f"/sessions/{session_id}/events"
        start_time = time.monotonic()
        last_event_time = start_time

        try:
            async with self._build_client() as client:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()
                    buffer = ""
                    async for line in response.aiter_lines():
                        now = time.monotonic()

                        # Session total timeout
                        if now - start_time > self._session_timeout:
                            raise OpenCodeTimeoutError(
                                f"SSE session {session_id} exceeded total "
                                f"timeout of {self._session_timeout}s"
                            )

                        # Idle timeout
                        if now - last_event_time > self._idle_timeout:
                            raise OpenCodeTimeoutError(
                                f"SSE session {session_id} idle timeout of "
                                f"{self._idle_timeout}s exceeded"
                            )

                        if line.strip() == "":
                            # Empty line = SSE event boundary
                            if buffer.strip():
                                event = self._parse_sse_event(buffer)
                                buffer = ""
                                if event is not None:
                                    last_event_time = time.monotonic()
                                    yield event
                        elif line.startswith("data:"):
                            buffer += line + "\n"
                        else:
                            # Other SSE fields (event:, id:, retry:)
                            buffer += line + "\n"

                    # Flush remaining buffer (stream ended without trailing newline)
                    if buffer.strip():
                        event = self._parse_sse_event(buffer)
                        if event is not None:
                            yield event

        except httpx.ConnectError as exc:
            raise OpenCodeConnectionError(
                f"SSE connection failed: {redact_text(str(exc))}"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise OpenCodeHTTPError(
                f"SSE HTTP {exc.response.status_code}: "
                f"{redact_text(str(exc))}"
            ) from exc
        except httpx.ReadTimeout as exc:
            raise OpenCodeTimeoutError(
                f"SSE read timed out: {redact_text(str(exc))}"
            ) from exc

    @staticmethod
    def _parse_sse_event(buffer: str) -> dict[str, Any] | None:
        """Parse SSE buffer into event dict.

        Extracts 'data:' lines, joins multiline data, attempts JSON parse.
        Falls back to raw text wrapped as plan.delta if JSON fails.
        Non-JSON chunks exceeding _SSE_CHUNK_SIZE_LIMIT are truncated with
        a metadata flag so the consumer can emit a warning event.
        Returns None if no data lines found.
        """
        data_lines: list[str] = []
        for line in buffer.split("\n"):
            line = line.strip()
            if line.startswith("data:"):
                data_lines.append(line[5:].strip())

        if not data_lines:
            return None

        data_str = "\n".join(data_lines)
        try:
            return json.loads(data_str)
        except json.JSONDecodeError:
            # Non-JSON SSE payload → wrap as raw delta with per-chunk size limit
            encoded = data_str.encode("utf-8")
            truncated = False
            if len(encoded) > RealOpenCodeHttpTransport._SSE_CHUNK_SIZE_LIMIT:
                safe = encoded[: RealOpenCodeHttpTransport._SSE_CHUNK_SIZE_LIMIT]
                data_str = safe.decode("utf-8", errors="replace")
                truncated = True
            event: dict[str, Any] = {"type": "plan.delta", "text": data_str}
            if truncated:
                event["_sse_chunk_truncated"] = True
            return event
