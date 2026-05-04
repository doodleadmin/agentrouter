"""OpenCode client abstraction and BE-03 plan-only stub implementation.

BE-05: added max_plan_size truncation, client-side timeout enforcement,
tool.call path confinement, and improved SSE robustness.
"""

from __future__ import annotations

import time
from typing import Any, Awaitable, Callable, Protocol

from app.config import settings
from app.integrations.opencode.schemas import (
    OpenCodeSessionMessageRequest,
    RuntimePlanContext,
    RuntimePlanResult,
)
from app.policy.runtime_guardrails import (
    ensure_path_confined,
    is_allowed_plan_action,
    redact_payload,
    redact_text,
)

# BE-07: internal mapped event types (post-mapper policy guard).
# OpenCode raw part types (text, reasoning, step-start, step-finish, tool)
# are handled by _map_message_response_to_events and NOT listed here.
KNOWN_SSE_EVENT_TYPES = frozenset({"plan.delta", "plan.final", "tool.call"})


class RuntimeEventError(Exception):
    """Structured runtime error code."""


class RuntimeConfigurationError(Exception):
    """Runtime provider configuration is invalid (fail-closed)."""


class OpenCodeTransportProtocol(Protocol):
    async def create_session(self, payload: dict[str, Any]) -> str: ...
    async def send_message(self, session_id: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class OpenCodeClientProtocol(Protocol):
    """Runtime adapter contract to enable future real OpenCode integration."""

    async def generate_plan(self, context: RuntimePlanContext) -> RuntimePlanResult:
        """Generate execution plan from task context without executing code."""


class StubOpenCodeClient:
    """Deterministic fake runtime adapter used for BE-03 plan-only mode."""

    async def generate_plan(self, context: RuntimePlanContext) -> RuntimePlanResult:
        plan = (
            "## Plan\n"
            f"1. Analyze task for project `{context.project_slug}` and agent `{context.agent_slug}`.\n"
            "2. Identify likely files/modules impacted by requested change.\n"
            "3. Propose validation steps and rollback considerations.\n\n"
            "## Task Context\n"
            f"- Agent role: {context.agent_role}\n"
            f"- Raw task: {context.raw_text}\n"
            f"- Normalized task: {context.normalized_text}\n"
            f"- Repo path: {context.repo_path}\n"
            f"- Memory path: {context.memory_path}\n\n"
            "## Safety\n"
            "- Mode: plan-only\n"
            "- No code execution\n"
            "- No file modifications\n"
        )
        return RuntimePlanResult(plan_text=plan, session_id="stub-session")


class FakeOpenCodeHttpClient:
    """Test helper: fake OpenCode HTTP/SSE client for deterministic tests."""

    def __init__(self, events: list[dict[str, Any]] | None = None) -> None:
        self._events = events or []
        self.last_payload: dict[str, Any] | None = None

    async def create_session(self, payload: dict[str, Any]) -> str:
        self.last_payload = redact_payload(payload)
        return "fake-session-1"

    async def send_message(self, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        _ = session_id
        _ = payload
        return {"parts": self._events}


class OpenCodeHttpPlanClient:
    """Plan-only OpenCode client using HTTP sync-message transport.

    BE-05 additions:
    - max_plan_size hard truncation with warning event
    - client-side session/idle timeout enforcement
    - tool.call path confinement for read/search actions
    - strict fail-closed message part classification (malformed vs unknown)
    """

    def __init__(
        self,
        transport: OpenCodeTransportProtocol,
        *,
        on_event: Callable[[str, dict[str, Any]], Awaitable[None]] | None = None,
        max_retries: int = 2,
        max_plan_bytes: int | None = None,
        session_timeout_sec: float | None = None,
        idle_timeout_sec: float | None = None,
    ) -> None:
        self._transport = transport
        self._on_event = on_event
        self._max_retries = max_retries
        self._max_plan_bytes = max_plan_bytes or settings.RUNTIME_MAX_PLAN_BYTES
        self._session_timeout = session_timeout_sec or float(settings.RUNTIME_SESSION_TIMEOUT_SECONDS)
        self._idle_timeout = idle_timeout_sec or float(settings.RUNTIME_IDLE_TIMEOUT_SECONDS)

    async def _emit(self, event_type: str, payload: dict[str, Any]) -> None:
        if self._on_event is not None:
            await self._on_event(event_type, redact_payload(payload))

    def _truncate_plan(self, plan_text: str, session_id: str) -> str:
        """Truncate plan text to _max_plan_bytes with hard boundary cut.

        BE-05 M-1: session_id is included in the truncation marker for
        traceability and debugging.
        """
        encoded = plan_text.encode("utf-8")
        if len(encoded) <= self._max_plan_bytes:
            return plan_text
        # Hard truncation: cut at byte boundary, replace broken tail
        safe = encoded[: self._max_plan_bytes]
        truncated = safe.decode("utf-8", errors="replace")
        return truncated + f"\n\n[TRUNCATED — plan exceeded max size] (session={session_id})"

    async def generate_plan(self, context: RuntimePlanContext) -> RuntimePlanResult:
        payload = {
            "mode": "plan_only",
            "correlation_id": context.correlation_id,
            "idempotency_key": context.idempotency_key,
            "input": {
                "project_slug": context.project_slug,
                "agent_slug": context.agent_slug,
                "task": context.normalized_text,
                "memory_chunks": context.memory_chunks,
            },
        }
        session_id = await self._transport.create_session(payload)

        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            plan_parts: list[str] = []
            final_received = False
            seen: set[tuple[str, str]] = set()
            session_start = time.monotonic()
            last_event_time = session_start

            try:
                # BE-07: contract-aligned parts-based payload
                message_response = await self._transport.send_message(
                    session_id,
                    OpenCodeSessionMessageRequest(
                        parts=[
                            {"type": "text", "text": context.normalized_text},
                        ]
                    ).model_dump(mode="json"),
                )
                for event in self._map_message_response_to_events(message_response):
                    now = time.monotonic()
                    if now - session_start > self._session_timeout:
                        raise TimeoutError("runtime_timeout")
                    if now - last_event_time > self._idle_timeout:
                        raise TimeoutError("runtime_timeout")
                    last_event_time = now
                    event_id = str(event.get("event_id") or event.get("seq") or "")
                    dedupe_key = (session_id, event_id)
                    if event_id and dedupe_key in seen:
                        await self._emit(
                            "runtime_duplicate_event_ignored",
                            {"session_id": session_id, "event_id": event_id},
                        )
                        continue
                    if event_id:
                        seen.add(dedupe_key)
                    await self._emit(
                        "runtime_event_received",
                        {
                            "session_id": session_id,
                            "event_id": event_id,
                            "type": event.get("type"),
                        },
                    )

                    event_type = event.get("type")

                    # --- SSE robustness: malformed (missing type) ---
                    if not event_type or not isinstance(event_type, str):
                        raise RuntimeEventError("runtime_event_malformed")

                    # --- SSE robustness: unknown event type ---
                    if event_type not in KNOWN_SSE_EVENT_TYPES:
                        raise RuntimeEventError("runtime_error")

                    # --- tool.call path confinement ---
                    if event_type == "tool.call":
                        action = str(event.get("action", ""))
                        path = event.get("path")
                        if action in {"read", "search"} and path is not None:
                            try:
                                ensure_path_confined(
                                    str(path), settings.RUNTIME_ALLOWED_ROOT
                                )
                            except ValueError:
                                await self._emit(
                                    "policy_blocked",
                                    {
                                        "session_id": session_id,
                                        "action": action,
                                        "path": redact_text(str(path)),
                                    },
                                )
                                raise PermissionError("policy_blocked")
                        if not is_allowed_plan_action(action):
                            raise PermissionError("policy_blocked")
                        continue

                    if event_type == "plan.delta":
                        text = str(event.get("text", ""))
                        plan_parts.append(str(redact_payload(text)))
                        continue

                    if event_type == "plan.final":
                        final_received = True

                if not final_received:
                    raise TimeoutError("runtime_timeout")

                plan_text = "".join(plan_parts).strip()
                if not plan_text:
                    raise RuntimeEventError("runtime_error")

                # --- max_plan_size enforcement ---
                if len(plan_text.encode("utf-8")) > self._max_plan_bytes:
                    await self._emit(
                        "runtime_event_truncated",
                        {
                            "session_id": session_id,
                            "limit": self._max_plan_bytes,
                            "actual_bytes": len(plan_text.encode("utf-8")),
                        },
                    )
                    plan_text = self._truncate_plan(plan_text, session_id)

                return RuntimePlanResult(
                    plan_text=plan_text,
                    session_id=session_id,
                )

            except TimeoutError as exc:
                last_exc = exc
                if attempt < self._max_retries:
                    await self._emit(
                        "runtime_retry_scheduled",
                        {"session_id": session_id, "attempt": attempt + 1},
                    )
                    continue
                break

        if last_exc:
            raise last_exc
        raise TimeoutError("runtime_timeout")

    @staticmethod
    def _map_message_response_to_events(response: dict[str, Any]) -> list[dict[str, Any]]:
        """Map OpenCode 1.14.33 sync message response to internal event stream.

        BE-07: actual OpenCode contract (proven via probe):
        Response shape:
        {
          "info": { ... metadata ... },
          "parts": [
            {"type": "step-start", ...},
            {"type": "reasoning", "text": "..."},
            {"type": "text", "text": "## Plan..."},
            {"type": "step-finish", "reason": "stop"}
          ]
        }

        Mapping rules:
        - response["info"]  → skip (metadata/audit only)
        - response["parts"] → REQUIRED (not response["content"])
        - part type "text"         → plan.delta (redacted text)
        - part type "reasoning"    → SKIP entirely (never in plan_text / events)
        - part type "step-start"   → skip (metadata-only, no plan content)
        - part type "step-finish"  → plan.final (if reason == "stop")
        - part type "tool"         → tool.call (action/path, policy guards apply)
        - unknown part type        → runtime_event_malformed → fail-closed
        - empty parts              → runtime_error
        - only reasoning/step-start (no text/tool/step-finish) → runtime_error
        """
        if not isinstance(response, dict):
            raise RuntimeEventError("runtime_event_malformed")

        # BE-07: parts is the REQUIRED field (not content fallback)
        parts = response.get("parts")
        if not isinstance(parts, list):
            raise RuntimeEventError("runtime_event_malformed")
        if len(parts) == 0:
            raise RuntimeEventError("runtime_error")

        events: list[dict[str, Any]] = []

        for idx, part in enumerate(parts, start=1):
            if not isinstance(part, dict):
                raise RuntimeEventError("runtime_event_malformed")

            part_type = part.get("type")
            if not isinstance(part_type, str):
                raise RuntimeEventError("runtime_event_malformed")

            # ── text → plan.delta ───────────────────────────────────
            if part_type == "text":
                text = part.get("text")
                if not isinstance(text, str):
                    raise RuntimeEventError("runtime_event_malformed")
                events.append({
                    "type": "plan.delta",
                    "text": text,
                    "event_id": str(idx),
                })
                continue

            # ── reasoning → SKIP (never leak to plan_text / events) ─
            if part_type == "reasoning":
                # BE-07: reasoning text is NEVER saved anywhere.
                # No plan.delta, no task_events payload with text content.
                continue

            # ── step-start → skip (metadata-only) ───────────────────
            if part_type == "step-start":
                continue

            # ── step-finish → plan.final ─────────────────────────────
            if part_type == "step-finish":
                reason = part.get("reason", "")
                if reason == "stop":
                    events.append({
                        "type": "plan.final",
                        "event_id": str(idx),
                    })
                # Non-"stop" reasons (tool, error): ignore for plan-only
                continue

            # ── tool → tool.call ─────────────────────────────────────
            if part_type == "tool":
                action = part.get("action")
                if not isinstance(action, str):
                    action = part.get("name")
                if not isinstance(action, str):
                    raise RuntimeEventError("runtime_event_malformed")
                event: dict[str, Any] = {
                    "type": "tool.call",
                    "action": action,
                    "event_id": str(idx),
                }
                if "path" in part:
                    event["path"] = part.get("path")
                events.append(event)
                continue

            # ── unknown part type → fail-closed ──────────────────────
            raise RuntimeEventError("runtime_event_malformed")

        # ── semantic checks after parsing all parts ──────────────────
        # BE-07: if only reasoning/step-start parts were present (no text,
        # no tool, no step-finish), fail-closed as runtime_error.
        # Tool parts must pass through so policy guard can inspect them.
        # The caller (generate_plan) handles empty plan_text separately.
        if len(events) == 0:
            # Only reasoning / step-start parts (no meaningful content)
            raise RuntimeEventError("runtime_error")

        return events
