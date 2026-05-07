"""Runtime router for BE-03 plan-only task planning.

SEC-01 Phase 2: Permission checks deferred to Phase 3.
See app/security/permissions.py for the PermissionEngine.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.schemas.task import TaskRead
from app.services.runtime_service import RuntimeService

router = APIRouter(prefix="/runtime", tags=["runtime"])


def _svc(s: AsyncSession = Depends(get_async_session)) -> RuntimeService:
    return RuntimeService(s)


@router.post("/tasks/{task_id}/plan", response_model=TaskRead)
async def plan_task_runtime(
    task_id: UUID,
    svc: RuntimeService = Depends(_svc),
) -> TaskRead:
    # TODO(SEC-01 Phase 3): Add PermissionEngine.can_execute_runtime() check here.
    # Currently stubbed — always allowed.
    try:
        task = await svc.generate_plan_for_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return TaskRead.model_validate(task)
