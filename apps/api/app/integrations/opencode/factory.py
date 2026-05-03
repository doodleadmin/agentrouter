"""Runtime client factory for provider wiring.

BE-05 M-3: opencode_http now requires explicit RUNTIME_ALLOW_REAL_OPENCODE_HTTP=True
to instantiate RealOpenCodeHttpTransport (fail-closed by default).
Explicit DI with transport_factory still supported for tests (requires allow flag).
"""

from __future__ import annotations

from typing import Callable

from app.config import settings
from app.integrations.opencode.client import (
    OpenCodeClientProtocol,
    OpenCodeHttpPlanClient,
    RuntimeConfigurationError,
    StubOpenCodeClient,
)


def build_runtime_client(
    *,
    transport_factory: Callable[[], object] | None = None,
    event_callback=None,
) -> OpenCodeClientProtocol:
    provider = settings.RUNTIME_PROVIDER.strip().lower()

    if provider == "stub":
        return StubOpenCodeClient()

    if provider == "opencode_http":
        if not settings.OPENCODE_SERVER_URL.strip():
            raise RuntimeConfigurationError(
                "RUNTIME_PROVIDER=opencode_http requires OPENCODE_SERVER_URL"
            )
        if not settings.RUNTIME_ALLOW_REAL_OPENCODE_HTTP:
            raise RuntimeConfigurationError(
                "RUNTIME_PROVIDER=opencode_http requires "
                "RUNTIME_ALLOW_REAL_OPENCODE_HTTP=True. "
                "Real OpenCode HTTP transport is disabled by default (fail-closed)."
            )
        if transport_factory is None:
            # Production path: use real HTTP/SSE transport
            from app.integrations.opencode.transport import RealOpenCodeHttpTransport
            transport = RealOpenCodeHttpTransport()
        else:
            # Test path: explicit DI with fake transport
            transport = transport_factory()
        return OpenCodeHttpPlanClient(
            transport=transport,
            on_event=event_callback,
            max_retries=settings.RUNTIME_MAX_RETRIES,
        )

    raise RuntimeConfigurationError(
        f"Unknown runtime provider: {settings.RUNTIME_PROVIDER}"
    )
