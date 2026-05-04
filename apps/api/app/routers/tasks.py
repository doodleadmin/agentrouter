"""Tasks router — CRUD with status enforcement + plan pipeline trigger."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ActorType, TaskStatus
from app.db.session import get_async_session
from app.integrations.queue import enqueue_agent_plan
from app.schemas.task import TaskCreate, TaskRead, TaskStatusUpdate, TaskUpdate
from app.services.task_event_service import TaskEventService
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _svc(s: AsyncSession = Depends(get_async_session)) -> TaskService:
    return TaskService(s)


def _event_svc(s: AsyncSession = Depends(get_async_session)) -> TaskEventService:
    return TaskEventService(s)


_TASK_404 = "Task not found"


def _map_integrity_error(exc: IntegrityError) -> HTTPException:
    code = getattr(getattr(exc, "orig", None), "pgcode", None)
    if code == "23503":  # foreign_key_violation
        return HTTPException(status_code=422, detail="Invalid project_id or agent_id reference")
    if code == "23505":  # unique_violation
        return HTTPException(status_code=409, detail="Task constraint conflict")
    return HTTPException(status_code=409, detail="Task integrity constraint violation")


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: TaskCreate,
    s: AsyncSession = Depends(get_async_session),
    svc: TaskService = Depends(_svc),
    esvc: TaskEventService = Depends(_event_svc),
) -> TaskRead:
    try:
        task = await svc.create(body)
        await esvc.create(task.id, "task_created", ActorType.SYSTEM)
        return TaskRead.model_validate(task)
    except IntegrityError as exc:
        await s.rollback()
        raise _map_integrity_error(exc) from exc


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    status_filter: str | None = Query(None, alias="status"),
    project_id: UUID | None = None,
    agent_id: UUID | None = None,
    risk_level: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    svc: TaskService = Depends(_svc),
) -> list[TaskRead]:
    results = await svc.list(
        status=status_filter,
        project_id=project_id,
        agent_id=agent_id,
        risk_level=risk_level,
        limit=limit,
        offset=offset,
    )
    return [TaskRead.model_validate(r) for r in results]


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: UUID,
    svc: TaskService = Depends(_svc),
) -> TaskRead:
    obj = await svc.get(task_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=_TASK_404)
    return TaskRead.model_validate(obj)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: UUID,
    body: TaskUpdate,
    svc: TaskService = Depends(_svc),
    esvc: TaskEventService = Depends(_event_svc),
) -> TaskRead:
    obj = await svc.update(task_id, body)
    if obj is None:
        raise HTTPException(status_code=404, detail=_TASK_404)
    await esvc.create(task_id, "task_updated", ActorType.SYSTEM)
    return TaskRead.model_validate(obj)


@router.patch("/{task_id}/status", response_model=TaskRead)
async def update_task_status(
    task_id: UUID,
    body: TaskStatusUpdate,
    svc: TaskService = Depends(_svc),
    esvc: TaskEventService = Depends(_event_svc),
) -> TaskRead:
    try:
        task = await svc.update_status(task_id, body)
    except KeyError:
        raise HTTPException(status_code=404, detail=_TASK_404)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    await esvc.create(task_id, f"status_changed_to_{body.status.value}", ActorType.SYSTEM)
    return TaskRead.model_validate(task)


@router.post("/{task_id}/cancel", response_model=TaskRead)
async def cancel_task(
    task_id: UUID,
    svc: TaskService = Depends(_svc),
    esvc: TaskEventService = Depends(_event_svc),
) -> TaskRead:
    try:
        task = await svc.cancel(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=_TASK_404)
    await esvc.create(task_id, "task_cancelled", ActorType.SYSTEM)
    return TaskRead.model_validate(task)


@router.post("/{task_id}/trigger-plan", response_model=TaskRead, status_code=status.HTTP_202_ACCEPTED)
async def trigger_plan(
    task_id: UUID,
    svc: TaskService = Depends(_svc),
    esvc: TaskEventService = Depends(_event_svc),
) -> TaskRead:
    """Validate and enqueue a task for plan generation via Celery.

    Pipeline: created → routed → (Celery agent_plan) → planning → approved/waiting_approval.
    """
    task = await svc.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=_TASK_404)

    # P0-2: Only CREATED tasks may be enqueued for planning.
    if task.status != TaskStatus.CREATED.value:
        raise HTTPException(
            status_code=409,
            detail="Task already triggered or not in created state",
        )

    if task.project_id is None or task.agent_id is None:
        raise HTTPException(
            status_code=422,
            detail="Task must have project_id and agent_id before planning.",
        )

    # Transition created → routed
    try:
        task = await svc.update_status(task_id, TaskStatusUpdate(status=TaskStatus.ROUTED))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    await esvc.create(task_id, "plan_triggered", ActorType.SYSTEM, payload={"source": "api"})

    # Dispatch to Celery agent_plan queue
    enqueue_agent_plan(str(task_id))

    return TaskRead.model_validate(task)
