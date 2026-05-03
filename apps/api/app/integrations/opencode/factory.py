"""Runtime client factory for provider wiring."""

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
        if transport_factory is None:
            raise RuntimeConfigurationError(
                "No transport configured for opencode_http (explicit DI required in tests)"
            )
        transport = transport_factory()
        return OpenCodeHttpPlanClient(
            transport=transport,
            on_event=event_callback,
            max_retries=settings.RUNTIME_MAX_RETRIES,
        )

    raise RuntimeConfigurationError(f"Unknown runtime provider: {settings.RUNTIME_PROVIDER}")
