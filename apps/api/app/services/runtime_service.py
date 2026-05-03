"""Runtime service for BE-03 plan-only adapter flow."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ActorType, RiskLevel, TaskStatus
from app.integrations.opencode.client import OpenCodeClientProtocol, StubOpenCodeClient
from app.integrations.opencode.schemas import RuntimePlanContext
from app.models.agent import Agent
from app.models.project import Project
from app.models.task import Task
from app.schemas.approval import ApprovalCreate
from app.schemas.task import TaskStatusUpdate, TaskUpdate
from app.services.approval_service import ApprovalService
from app.services.task_event_service import TaskEventService
from app.services.task_service import TaskService


class RuntimeService:
    """Builds task plans via runtime adapter without executing any code."""

    def __init__(
        self,
        session: AsyncSession,
        runtime_client: OpenCodeClientProtocol | None = None,
    ) -> None:
        self._session = session
        self._runtime_client = runtime_client or StubOpenCodeClient()
        self._tasks = TaskService(session)
        self._events = TaskEventService(session)
        self._approvals = ApprovalService(session)

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

        # planning phase marker (explicit per BE-03 requirements)
        planning_stmt = (
            update(Task)
            .where(Task.id == task_id)
            .values(status=TaskStatus.PLANNING.value)
            .returning(Task)
        )
        planning_result = await self._session.execute(planning_stmt)
        task = planning_result.scalar_one_or_none()
        if task is None:
            raise KeyError("Task not found")

        context = RuntimePlanContext(
            project_slug=project.slug,
            repo_path=project.repo_path,
            memory_path=project.memory_path,
            agent_slug=agent.slug,
            agent_role=agent.role,
            raw_text=task.raw_text,
            normalized_text=task.normalized_text,
        )

        result = await self._runtime_client.generate_plan(context)

        # Persist plan text
        task = await self._tasks.update(
            task_id,
            TaskUpdate(plan_text=result.plan_text),
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
