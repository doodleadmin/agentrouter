"""Approvals router — create request, approve, reject (SEC-01 wired)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.enums import TaskStatus
from app.db.session import get_async_session
from app.schemas.approval import ApprovalCreate, ApprovalDecideIn, ApprovalRead
from app.schemas.task import TaskStatusUpdate
from app.security.context import context_for_telegram_user
from app.security.permissions import PermissionAction, PermissionEngine
from app.services.approval_service import ApprovalService
from app.services.task_service import TaskService

router = APIRouter(prefix="/approvals", tags=["approvals"])


def _engine() -> PermissionEngine:
    return PermissionEngine(admin_user_ids=settings.admin_user_ids)


def _svc(s: AsyncSession = Depends(get_async_session)) -> ApprovalService:
    return ApprovalService(s)


def _task_svc(s: AsyncSession = Depends(get_async_session)) -> TaskService:
    return TaskService(s)


_APPROVAL_404 = "Approval not found"


@router.post("/tasks/{task_id}/approvals", response_model=ApprovalRead, status_code=status.HTTP_201_CREATED)
async def create_approval(
    task_id: UUID,
    body: ApprovalCreate,
    svc: ApprovalService = Depends(_svc),
) -> ApprovalRead:
    obj = await svc.create_request(task_id, body)
    return ApprovalRead.model_validate(obj)


@router.get("/tasks/{task_id}/approvals", response_model=list[ApprovalRead])
async def list_approvals_by_task(
    task_id: UUID,
    svc: ApprovalService = Depends(_svc),
) -> list[ApprovalRead]:
    results = await svc.list_by_task(task_id)
    return [ApprovalRead.model_validate(r) for r in results]


@router.get("/{approval_id}", response_model=ApprovalRead)
async def get_approval(
    approval_id: UUID,
    svc: ApprovalService = Depends(_svc),
) -> ApprovalRead:
    obj = await svc.get(approval_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=_APPROVAL_404)
    return ApprovalRead.model_validate(obj)


@router.post("/{approval_id}/approve", response_model=ApprovalRead)
async def approve_approval(
    approval_id: UUID,
    body: ApprovalDecideIn | None = None,
    svc: ApprovalService = Depends(_svc),
    task_svc: TaskService = Depends(_task_svc),
) -> ApprovalRead:
    # SEC-01: permission check — admin-gated
    engine = _engine()
    user_id = str(body.approved_by) if body and body.approved_by is not None else None
    ctx = context_for_telegram_user(
        user_id=user_id or "0",
        action=PermissionAction.APPROVE,
        task_id=str(approval_id),  # temporary — will resolve task_id below
    )
    decision = engine.can_approve(ctx)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)

    try:
        obj = await svc.approve(approval_id, body)
    except KeyError:
        raise HTTPException(status_code=404, detail=_APPROVAL_404)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    # Transition task: waiting_approval → approved
    try:
        await task_svc.update_status(
            obj.task_id, TaskStatusUpdate(status=TaskStatus.APPROVED)
        )
    except (KeyError, ValueError):
        pass  # task already moved or not found — non-fatal

    return ApprovalRead.model_validate(obj)


@router.post("/{approval_id}/reject", response_model=ApprovalRead)
async def reject_approval(
    approval_id: UUID,
    body: ApprovalDecideIn | None = None,
    svc: ApprovalService = Depends(_svc),
    task_svc: TaskService = Depends(_task_svc),
) -> ApprovalRead:
    # SEC-01: permission check — admin-gated
    engine = _engine()
    user_id = str(body.approved_by) if body and body.approved_by is not None else None
    ctx = context_for_telegram_user(
        user_id=user_id or "0",
        action=PermissionAction.REJECT,
        task_id=str(approval_id),
    )
    decision = engine.can_reject(ctx)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)

    try:
        obj = await svc.reject(approval_id, body)
    except KeyError:
        raise HTTPException(status_code=404, detail=_APPROVAL_404)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    # Transition task: waiting_approval → cancelled
    try:
        await task_svc.update_status(
            obj.task_id, TaskStatusUpdate(status=TaskStatus.CANCELLED)
        )
    except (KeyError, ValueError):
        pass  # task already moved or not found — non-fatal

    return ApprovalRead.model_validate(obj)
