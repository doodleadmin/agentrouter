"""Approvals router — create request, approve, reject."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.schemas.approval import ApprovalCreate, ApprovalDecideIn, ApprovalRead
from app.services.approval_service import ApprovalService

router = APIRouter(prefix="/approvals", tags=["approvals"])


def _svc(s: AsyncSession = Depends(get_async_session)) -> ApprovalService:
    return ApprovalService(s)


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
) -> ApprovalRead:
    try:
        obj = await svc.approve(approval_id, body)
    except KeyError:
        raise HTTPException(status_code=404, detail=_APPROVAL_404)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return ApprovalRead.model_validate(obj)


@router.post("/{approval_id}/reject", response_model=ApprovalRead)
async def reject_approval(
    approval_id: UUID,
    body: ApprovalDecideIn | None = None,
    svc: ApprovalService = Depends(_svc),
) -> ApprovalRead:
    try:
        obj = await svc.reject(approval_id, body)
    except KeyError:
        raise HTTPException(status_code=404, detail=_APPROVAL_404)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return ApprovalRead.model_validate(obj)
