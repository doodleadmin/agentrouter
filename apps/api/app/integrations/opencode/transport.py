"""RealOpenCodeHttpTransport — HTTP transport to OpenCode server via httpx."""

from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


class OpenCodeTransportError(Exception):
    """Transport-level error."""


class OpenCodeConnectionError(OpenCodeTransportError):
    """Failed to connect to OpenCode server."""


class OpenCodeTimeoutError(OpenCodeTransportError):
    """Request to OpenCode server timed out."""


class OpenCodeHTTPError(OpenCodeTransportError):
    """OpenCode server returned HTTP error."""


class RealOpenCodeHttpTransport:
    """Production HTTP transport to a real OpenCode server.

    Implements OpenCodeTransportProtocol (create_session + send_message).
    Uses httpx.AsyncClient with configurable timeouts. Handles connection
    errors, HTTP status errors, and read timeouts with domain exceptions.
    Applies redaction to URL params and error messages that may contain secrets.
    """

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
        self._session_timeout = session_timeout or float(settings.RUNTIME_SESSION_TIMEOUT_SECONDS)
        # Fail-closed default: never allow unbounded read timeout in production path.
        self._read_timeout = self._session_timeout if read_timeout is None else read_timeout
        self._write_timeout = write_timeout
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
        return url

    async def create_session(self, payload: dict[str, Any]) -> str:
        """POST /session — create a new OpenCode session, return session_id."""
        try:
            async with self._build_client() as client:
                resp = await client.post("/session", json=payload)
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
                f"Failed to connect to OpenCode: {str(exc)}"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise OpenCodeHTTPError(
                f"OpenCode HTTP {exc.response.status_code}: "
                f"{str(exc)}"
            ) from exc
        except httpx.ReadTimeout as exc:
            raise OpenCodeTimeoutError(
                f"OpenCode session creation timed out: {str(exc)}"
            ) from exc

    async def send_message(self, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /session/{id}/message — sync message response payload.

        Read timeout is disabled (read=None) to match OpenCode SDK behaviour
        (req.timeout=false). Client-side session/idle timeout in
        OpenCodeHttpPlanClient provides the safety net.
        """
        url = f"/session/{session_id}/message"
        timeout_no_read = httpx.Timeout(
            connect=self._connect_timeout,
            read=None,
            write=self._write_timeout,
            pool=self._connect_timeout,
        )
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=timeout_no_read
            ) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                if not isinstance(data, dict):
                    raise OpenCodeTransportError("message response must be a JSON object")
                return data

        except httpx.ConnectError as exc:
            raise OpenCodeConnectionError(
                f"Message request failed: {str(exc)}"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise OpenCodeHTTPError(
                f"Message HTTP {exc.response.status_code}: "
                f"{str(exc)}"
            ) from exc
        except (httpx.ReadTimeout, httpx.ReadError) as exc:
            raise OpenCodeTimeoutError(
                f"Message request failed (read error/timeout): {str(exc)}"
            ) from exc
