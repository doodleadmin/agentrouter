"""Runtime service for BE-03 plan-only adapter flow."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.enums import ActorType, RiskLevel, TaskStatus
from app.integrations.opencode.client import (
    OpenCodeClientProtocol,
    OpenCodeHttpPlanClient,
    RuntimeEventError,
)
from app.integrations.opencode.factory import build_runtime_client
from app.integrations.opencode.schemas import RuntimePlanContext
from app.models.agent import Agent
from app.models.project import Project
from app.models.task import Task
from app.policy.runtime_guardrails import ensure_path_confined, redact_payload, redact_text
from app.schemas.approval import ApprovalCreate
from app.schemas.task import TaskStatusUpdate, TaskUpdate
from app.services.approval_service import ApprovalService
from app.services.memory_retrieval_service import (
    MemoryRetrievalService,
    SqlAlchemyRetrievalRepository,
)
from app.services.task_event_service import TaskEventService
from app.services.task_service import TaskService


class RuntimeService:
    """Builds task plans via runtime adapter without executing any code."""

    def __init__(
        self,
        session: AsyncSession,
        runtime_client: OpenCodeClientProtocol | None = None,
        runtime_transport_factory: Callable[[], object] | None = None,
    ) -> None:
        self._session = session
        self._runtime_client = runtime_client
        self._runtime_transport_factory = runtime_transport_factory
        self._tasks = TaskService(session)
        self._events = TaskEventService(session)
        self._approvals = ApprovalService(session)

    async def _emit_runtime_event(self, task_id: UUID, event_type: str, payload: dict) -> None:
        await self._events.create(
            task_id=task_id,
            event_type=event_type,
            actor_type=ActorType.SYSTEM,
            payload=redact_payload(payload),
        )

    def _resolve_runtime_client(self, task_id: UUID) -> OpenCodeClientProtocol:
        if self._runtime_client is not None:
            # Wire _on_event callback for DI-provided clients so that events
            # emitted inside generate_plan() (runtime_session_created, retry, etc.)
            # are persisted to the task event log.
            if isinstance(self._runtime_client, OpenCodeHttpPlanClient) and self._runtime_client._on_event is None:

                async def _callback(event_type: str, payload: dict) -> None:
                    await self._emit_runtime_event(task_id, event_type, payload)

                self._runtime_client._on_event = _callback
            return self._runtime_client

        async def _callback(event_type: str, payload: dict) -> None:
            await self._emit_runtime_event(task_id, event_type, payload)

        return build_runtime_client(
            transport_factory=self._runtime_transport_factory,
            event_callback=_callback,
        )

    async def _build_memory_chunks(self, query: str, project_slug: str) -> list[str]:
        retrieval = MemoryRetrievalService(SqlAlchemyRetrievalRepository(self._session))
        items = await retrieval.search(query=query, project_slug=project_slug, limit=settings.RUNTIME_MEMORY_TOP_K)
        return [redact_text(i.content) for i in items]

    async def _get_task_with_context(self, task_id: UUID) -> tuple[Task, Project, Agent]:
        task = await self._tasks.get(task_id)
        if task is None:
            raise KeyError("Task not found")
        if task.project_id is None:
            raise ValueError("Task is missing project_id")
        if task.agent_id is None:
            raise ValueError("Task is missing agent_id")

        project = await self._session.get(Project, task.project_id)
        if project is None:
            raise KeyError("Project not found for task")

        agent = await self._session.get(Agent, task.agent_id)
        if agent is None:
            raise KeyError("Agent not found for task")

        return task, project, agent

    async def generate_plan_for_task(self, task_id: UUID) -> Task:
        """Generate plan-only text and update task state + approvals/events."""
        task, project, agent = await self._get_task_with_context(task_id)

        corr_id = f"task:{task_id}:plan"
        idem_key = f"plan:{task_id}:v1"
        payload = task.payload or {}

        # P0-1: Status-based idempotency guard BEFORE PLANNING transition.
        # Block re-entry for in-flight (PLANNING) and terminal success states.
        # FAILED and CANCELLED are retryable (they represent terminal failures).
        if task.status in {
            TaskStatus.PLANNING.value,
            TaskStatus.APPROVED.value,
            TaskStatus.WAITING_APPROVAL.value,
            TaskStatus.COMPLETED.value,
        }:
            return task

        # Transition to PLANNING via validated TaskService method (not raw SQL).
        # This enforces allowed transitions (ROUTED→PLANNING) and prevents
        # double-entry race conditions.
        try:
            task = await self._tasks.update_status(
                task_id,
                TaskStatusUpdate(status=TaskStatus.PLANNING),
            )
        except ValueError:
            # Illegal transition — a concurrent call may have already entered PLANNING.
            # Re-read and return idempotently if the task is now in a guarded state.
            task = await self._tasks.get(task_id)
            if task is None:
                raise KeyError("Task not found")
            if task.status in {
                TaskStatus.PLANNING.value,
                TaskStatus.APPROVED.value,
                TaskStatus.WAITING_APPROVAL.value,
                TaskStatus.COMPLETED.value,
            }:
                return task
            raise

        try:
            runtime_client = self._resolve_runtime_client(task_id)
        except Exception as exc:
            await self._events.create(
                task_id=task_id,
                event_type="runtime_error",
                actor_type=ActorType.SYSTEM,
                payload=redact_payload({"error": str(exc)}),
            )
            task = await self._tasks.update_status(task_id, TaskStatusUpdate(status=TaskStatus.FAILED))
            await self._events.create(task_id=task_id, event_type="task_failed", actor_type=ActorType.SYSTEM)
            return task

        try:
            confined_repo = ensure_path_confined(project.repo_path, settings.RUNTIME_ALLOWED_ROOT)
            confined_memory = ensure_path_confined(project.memory_path, settings.RUNTIME_ALLOWED_ROOT)
        except ValueError as exc:
            await self._events.create(
                task_id=task_id,
                event_type="policy_blocked",
                actor_type=ActorType.SYSTEM,
                payload={"reason": redact_text(str(exc))},
            )
            task = await self._tasks.update_status(task_id, TaskStatusUpdate(status=TaskStatus.FAILED))
            await self._events.create(task_id=task_id, event_type="task_failed", actor_type=ActorType.SYSTEM)
            return task

        memory_chunks = await self._build_memory_chunks(task.normalized_text, project.slug)
        context = RuntimePlanContext(
            project_slug=project.slug,
            repo_path=confined_repo,
            memory_path=confined_memory,
            agent_slug=agent.slug,
            agent_role=agent.role,
            raw_text=redact_text(task.raw_text),
            normalized_text=redact_text(task.normalized_text),
            correlation_id=corr_id,
            idempotency_key=idem_key,
            memory_chunks=memory_chunks,
            task_title=task.title or "",
        )

        try:
            result = await runtime_client.generate_plan(context)
        except PermissionError as exc:
            await self._events.create(
                task_id=task_id,
                event_type="policy_blocked",
                actor_type=ActorType.SYSTEM,
                payload={"reason": redact_text(str(exc))},
            )
            task = await self._tasks.update_status(task_id, TaskStatusUpdate(status=TaskStatus.FAILED))
            await self._events.create(task_id=task_id, event_type="task_failed", actor_type=ActorType.SYSTEM)
            return task
        except TimeoutError as exc:
            await self._events.create(
                task_id=task_id,
                event_type="runtime_timeout",
                actor_type=ActorType.SYSTEM,
                payload={"reason": redact_text(str(exc)), "retry": 0},
            )
            task = await self._tasks.update_status(task_id, TaskStatusUpdate(status=TaskStatus.FAILED))
            await self._events.create(task_id=task_id, event_type="task_failed", actor_type=ActorType.SYSTEM)
            return task
        except RuntimeEventError as exc:
            code = str(exc)
            if code == "runtime_event_malformed":
                await self._events.create(
                    task_id=task_id,
                    event_type="runtime_event_malformed",
                    actor_type=ActorType.SYSTEM,
                    payload={"reason": code},
                )
            await self._events.create(
                task_id=task_id,
                event_type="runtime_error",
                actor_type=ActorType.SYSTEM,
                payload=redact_payload({"error": code}),
            )
            task = await self._tasks.update_status(task_id, TaskStatusUpdate(status=TaskStatus.FAILED))
            await self._events.create(task_id=task_id, event_type="task_failed", actor_type=ActorType.SYSTEM)
            return task
        except Exception as exc:
            await self._events.create(
                task_id=task_id,
                event_type="runtime_error",
                actor_type=ActorType.SYSTEM,
                payload=redact_payload({"error": str(exc)}),
            )
            task = await self._tasks.update_status(task_id, TaskStatusUpdate(status=TaskStatus.FAILED))
            await self._events.create(task_id=task_id, event_type="task_failed", actor_type=ActorType.SYSTEM)
            return task

        # Persist plan text
        # NOTE: runtime_session_created is now emitted inside generate_plan()
        # (via _on_event callback) BEFORE the retry loop — see P2-5.
        task = await self._tasks.update(
            task_id,
            TaskUpdate(
                plan_text=redact_text(result.plan_text),
                payload={
                    **payload,
                    "runtime_plan": {
                        "correlation_id": corr_id,
                        "session_id": result.session_id,
                        "idempotency_key": idem_key,
                    },
                },
            ),
        )
        if task is None:
            raise KeyError("Task not found")

        await self._events.create(
            task_id=task_id,
            event_type="plan_generated",
            actor_type=ActorType.SYSTEM,
            payload={"mode": "plan_only"},
        )

        risk = RiskLevel(task.risk_level)
        if risk is RiskLevel.LOW:
            task = await self._tasks.update_status(
                task_id,
                TaskStatusUpdate(status=TaskStatus.APPROVED),
            )
            return task

        # medium/high/critical require approval request
        task = await self._tasks.update_status(
            task_id,
            TaskStatusUpdate(status=TaskStatus.WAITING_APPROVAL),
        )

        await self._approvals.create_request(
            task_id=task_id,
            data=ApprovalCreate(
                action=task.intent or "task_execution",
                requested_by_agent_id=task.agent_id,
                payload={"source": "runtime_plan_only", "risk_level": task.risk_level},
            ),
        )
        # ApprovalService already logs approval_requested event.
        return task
