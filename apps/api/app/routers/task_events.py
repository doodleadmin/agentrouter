"""Task events router — audit trail list + internal create."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ActorType
from app.db.session import get_async_session
from app.schemas.task_event import TaskEventCreate, TaskEventRead
from app.services.task_event_service import TaskEventService

router = APIRouter(prefix="/events", tags=["task_events"])


def _svc(s: AsyncSession = Depends(get_async_session)) -> TaskEventService:
    return TaskEventService(s)


@router.get("", response_model=list[TaskEventRead])
async def list_events(
    task_id: UUID | None = Query(None),
    event_type: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    svc: TaskEventService = Depends(_svc),
) -> list[TaskEventRead]:
    results = await svc.list_all(
        task_id=task_id,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )
    return [TaskEventRead.model_validate(r) for r in results]


@router.get("/tasks/{task_id}/events", response_model=list[TaskEventRead])
async def list_events_by_task(
    task_id: UUID,
    svc: TaskEventService = Depends(_svc),
) -> list[TaskEventRead]:
    results = await svc.list_by_task(task_id)
    return [TaskEventRead.model_validate(r) for r in results]


@router.post("/tasks/{task_id}/events", response_model=TaskEventRead)
async def create_event(
    task_id: UUID,
    body: TaskEventCreate,
    svc: TaskEventService = Depends(_svc),
) -> TaskEventRead:
    try:
        actor_type = ActorType(body.actor_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    event = await svc.create(
        task_id,
        body.event_type,
        actor_type,
        actor_id=body.actor_id,
        payload=body.payload,
    )
    return TaskEventRead.model_validate(event)
