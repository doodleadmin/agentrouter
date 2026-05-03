"""OpenCode client abstraction and BE-03 plan-only stub implementation."""

from __future__ import annotations

from typing import Any, AsyncIterator, Awaitable, Callable, Protocol

from app.integrations.opencode.schemas import RuntimePlanContext, RuntimePlanResult
from app.policy.runtime_guardrails import is_allowed_plan_action, redact_payload


class RuntimeEventError(Exception):
    """Structured runtime error code."""


class RuntimeConfigurationError(Exception):
    """Runtime provider configuration is invalid (fail-closed)."""


class OpenCodeTransportProtocol(Protocol):
    async def create_session(self, payload: dict[str, Any]) -> str: ...
    async def stream_events(self, session_id: str) -> AsyncIterator[dict[str, Any]]: ...


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

    async def stream_events(self, session_id: str) -> AsyncIterator[dict[str, Any]]:
        for event in self._events:
            yield event


class OpenCodeHttpPlanClient:
    """Plan-only OpenCode client using fake/mocked HTTP+SSE contract."""

    def __init__(
        self,
        transport: OpenCodeTransportProtocol,
        *,
        on_event: Callable[[str, dict[str, Any]], Awaitable[None]] | None = None,
        max_retries: int = 2,
    ) -> None:
        self._transport = transport
        self._on_event = on_event
        self._max_retries = max_retries

    async def _emit(self, event_type: str, payload: dict[str, Any]) -> None:
        if self._on_event is not None:
            await self._on_event(event_type, redact_payload(payload))

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

            try:
                async for event in self._transport.stream_events(session_id):
                    event_id = str(event.get("event_id") or event.get("seq") or "")
                    dedupe_key = (session_id, event_id)
                    if event_id and dedupe_key in seen:
                        await self._emit("runtime_duplicate_event_ignored", {"session_id": session_id, "event_id": event_id})
                        continue
                    if event_id:
                        seen.add(dedupe_key)
                    await self._emit("runtime_event_received", {"session_id": session_id, "event_id": event_id, "type": event.get("type")})

                    event_type = event.get("type")
                    if event_type not in {"plan.delta", "plan.final", "tool.call"}:
                        raise RuntimeEventError("runtime_event_malformed")

                    if event_type == "tool.call":
                        action = str(event.get("action", ""))
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
                return RuntimePlanResult(plan_text="".join(plan_parts).strip(), session_id=session_id)
            except TimeoutError as exc:
                last_exc = exc
                if attempt < self._max_retries:
                    await self._emit("runtime_retry_scheduled", {"session_id": session_id, "attempt": attempt + 1})
                    continue
                break

        if last_exc:
            raise last_exc
        raise TimeoutError("runtime_timeout")
