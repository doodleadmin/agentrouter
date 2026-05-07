"""Tasks router — CRUD with status enforcement + plan pipeline trigger + SEC-01 permission checks."""

import hashlib
import hmac
import re
import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.enums import ActorType, ApprovalStatus, RiskLevel, TaskStatus
from app.db.session import get_async_session
from app.integrations.queue import enqueue_agent_plan
from app.schemas.task import (
    CallbackAnswerIn,
    CallbackAnswerRead,
    TaskCreate,
    TaskPlanRead,
    TaskRead,
    TaskStatusUpdate,
    TaskUpdate,
)
from app.security.context import context_for_callback, context_for_system, context_for_telegram_user
from app.security.permissions import PermissionAction, PermissionEngine
from app.services.approval_service import ApprovalService
from app.services.task_event_service import TaskEventService
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _engine() -> PermissionEngine:
    return PermissionEngine(admin_user_ids=settings.admin_user_ids)


def _svc(s: AsyncSession = Depends(get_async_session)) -> TaskService:
    return TaskService(s)


def _event_svc(s: AsyncSession = Depends(get_async_session)) -> TaskEventService:
    return TaskEventService(s)


def _appr_svc(s: AsyncSession = Depends(get_async_session)) -> ApprovalService:
    return ApprovalService(s)


_TASK_404 = "Task not found"

# ── callback data helpers ──────────────────────────────────────────────

CALLBACK_FIELD_SEP = "|"
CALLBACK_VERSION = 1  # v1 protocol: 6 fields + sig
COMPACT_CALLBACK_SEP = ":"
COMPACT_CALLBACK_VERSION = "v1"
COMPACT_ACTION_ALIASES = {
    "a": "approve",
    "r": "reject",
    "f": "refresh",
    "p": "show_plan",
    "t": "show_task",
}
COMPACT_EXTERNAL_ID_RE = re.compile(r"^task-[0-9]{4,}$")
COMPACT_EXP_RE = re.compile(r"^[0-9a-z]+$")
COMPACT_SIG_RE = re.compile(r"^[0-9a-f]{16}$")


def _parse_callback_fields(data: str) -> dict[str, str] | None:
    """Parse v1 callback data: version|action|task_id|approval_id|rev|exp|sig"""
    parts = data.split(CALLBACK_FIELD_SEP)
    if len(parts) != 7:
        return None
    try:
        version = int(parts[0])
    except (ValueError, TypeError):
        return None
    if version != CALLBACK_VERSION:
        return None
    return {
        "protocol": "legacy",
        "version": parts[0],
        "action": parts[1],
        "task_id": parts[2],
        "approval_id": parts[3],
        "rev": parts[4],
        "exp": parts[5],
        "sig": parts[6],
    }


def _parse_compact_callback_fields(data: str) -> dict[str, str] | None:
    """Parse compact v1 callback data: v1:<alias>:<external_id>:<exp36>:<sig16>."""
    parts = data.split(COMPACT_CALLBACK_SEP)
    if len(parts) != 5:
        return None
    version, alias, external_id, exp_base36, sig = parts
    if version != COMPACT_CALLBACK_VERSION:
        return None
    if alias not in COMPACT_ACTION_ALIASES:
        raise ValueError("Unknown callback action")
    if not COMPACT_EXTERNAL_ID_RE.fullmatch(external_id):
        raise ValueError("Invalid task external_id in callback_data")
    if not COMPACT_EXP_RE.fullmatch(exp_base36):
        raise ValueError("Invalid expiry in callback_data")
    if not COMPACT_SIG_RE.fullmatch(sig):
        raise ValueError("Invalid callback_data signature")
    return {
        "protocol": "compact",
        "version": version,
        "alias": alias,
        "action": COMPACT_ACTION_ALIASES[alias],
        "task_external_id": external_id,
        "exp": exp_base36,
        "sig": sig,
    }


def _compute_callback_signature(base: str) -> str:
    """HMAC-SHA256 of the base string (fields 0-5 joined by |)."""
    secret = settings.CALLBACK_SECRET.encode("utf-8") if settings.CALLBACK_SECRET else b""
    return hmac.new(secret, base.encode("utf-8"), hashlib.sha256).hexdigest()


def _base36_to_int(value: str) -> int:
    try:
        return int(value, 36)
    except (TypeError, ValueError):
        raise ValueError("Invalid expiry in callback_data") from None


def _validate_compact_callback_data(callback_data: str) -> dict[str, str]:
    fields = _parse_compact_callback_fields(callback_data)
    if fields is None:
        raise ValueError("Invalid callback_data format")

    signing_payload = (
        f"{COMPACT_CALLBACK_VERSION}|{fields['alias']}|"
        f"{fields['task_external_id']}|{fields['exp']}"
    )
    expected_sig = _compute_callback_signature(signing_payload)[:16]
    if not hmac.compare_digest(fields["sig"], expected_sig):
        raise ValueError("Invalid callback_data signature")

    if time.time() > _base36_to_int(fields["exp"]):
        raise ValueError("Callback data expired")

    return fields


def _validate_callback_data(callback_data: str) -> dict[str, str]:
    """
    Validate callback_data: parse, check signature, check expiry.
    Returns parsed fields on success. Raises ValueError on validation failure.
    """
    if callback_data.startswith(f"{COMPACT_CALLBACK_VERSION}{COMPACT_CALLBACK_SEP}"):
        return _validate_compact_callback_data(callback_data)

    fields = _parse_callback_fields(callback_data)
    if fields is None:
        raise ValueError("Invalid callback_data format")

    if fields["action"] not in set(COMPACT_ACTION_ALIASES.values()):
        raise ValueError("Unknown callback action")

    # Signature check: base = everything except last field
    base = CALLBACK_FIELD_SEP.join(callback_data.split(CALLBACK_FIELD_SEP)[:6])
    expected_sig = _compute_callback_signature(base)
    if not hmac.compare_digest(fields["sig"], expected_sig):
        raise ValueError("Invalid callback_data signature")

    # Expiry check
    try:
        exp = int(fields["exp"])
    except (ValueError, TypeError):
        raise ValueError("Invalid expiry in callback_data")
    if time.time() > exp:
        raise ValueError("Callback data expired")

    return fields


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
    # SEC-01: permission check — system actors allowed, others need approval
    engine = _engine()
    ctx = context_for_system(action=PermissionAction.UPDATE_STATUS, task_id=str(task_id))
    decision = engine.can_update_status(ctx)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)

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
    triggered_by: int | None = Query(None, description="Telegram user ID of the requester"),
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

    # SEC-01: permission check — risk-level gating
    engine = _engine()
    try:
        risk_level = RiskLevel(task.risk_level) if task.risk_level else RiskLevel.LOW
    except ValueError:
        risk_level = RiskLevel.LOW
    ctx = context_for_telegram_user(
        user_id=str(triggered_by) if triggered_by is not None else "0",
        action=PermissionAction.TRIGGER_PLAN,
        task_id=str(task_id),
        project_id=str(task.project_id),
        agent_id=str(task.agent_id),
        risk_level=risk_level,
    )
    decision = engine.can_trigger_plan(ctx)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)
    # Note: requires_approval flag is advisory for now; existing flow
    # already handles medium-risk tasks with approval creation elsewhere.

    # Transition created → routed
    try:
        task = await svc.update_status(task_id, TaskStatusUpdate(status=TaskStatus.ROUTED))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    await esvc.create(task_id, "plan_triggered", ActorType.SYSTEM, payload={"source": "api"})

    # Dispatch to Celery agent_plan queue
    enqueue_agent_plan(str(task_id))

    return TaskRead.model_validate(task)


@router.get("/{task_id}/plan", response_model=TaskPlanRead)
async def get_task_plan(
    task_id: UUID,
    svc: TaskService = Depends(_svc),
) -> TaskPlanRead:
    """Return the current plan_text for a task."""
    obj = await svc.get(task_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=_TASK_404)
    return TaskPlanRead(
        task_id=obj.id,
        plan_text=obj.plan_text,
        plan_version=1,
        status=obj.status,
    )


@router.post("/{task_id}/callback-answer", response_model=CallbackAnswerRead)
async def callback_answer(
    task_id: UUID,
    body: CallbackAnswerIn,
    svc: TaskService = Depends(_svc),
    esvc: TaskEventService = Depends(_event_svc),
    asvc: ApprovalService = Depends(_appr_svc),
) -> CallbackAnswerRead:
    """Validate a Telegram inline-button callback and return task+approval state.

    Used by the bot for UI feedback on button clicks (approve/reject/show-plan/refresh).
    Validation happens API-side for security.
    """
    # 1. Validate callback_data cryptographically
    try:
        fields = _validate_callback_data(body.callback_data)
    except ValueError as exc:
        return CallbackAnswerRead(
            task_id=task_id,
            task_status="unknown",
            task_external_id="",
            action_valid=False,
            action="unknown",
            error=str(exc),
        )

    action = fields["action"]

    # 2. Load task
    task = await svc.get(task_id)
    if task is None:
        return CallbackAnswerRead(
            task_id=task_id,
            task_status="unknown",
            task_external_id="",
            action_valid=False,
            action=action,
            error="Task not found",
        )

    # Compact callbacks bind to the short external_id; legacy callbacks bind to UUID.
    if fields.get("protocol") == "compact" and fields.get("task_external_id") != task.external_id:
        return CallbackAnswerRead(
            task_id=task_id,
            task_status=task.status,
            task_external_id=task.external_id,
            action_valid=False,
            action=action,
            error="Task external_id mismatch",
        )
    if fields.get("protocol") == "legacy" and fields.get("task_id") != str(task_id):
        return CallbackAnswerRead(
            task_id=task_id,
            task_status=task.status,
            task_external_id=task.external_id,
            action_valid=False,
            action=action,
            error="Task id mismatch",
        )

    # 3. Validate chat/thread/user constraints if provided
    if body.telegram_chat_id is not None and task.telegram_chat_id is not None:
        if body.telegram_chat_id != task.telegram_chat_id:
            return CallbackAnswerRead(
                task_id=task_id,
                task_status=task.status,
                task_external_id=task.external_id,
                action_valid=False,
                action=action,
                error="Chat mismatch",
            )
    if body.telegram_thread_id is not None and task.telegram_thread_id is not None:
        if body.telegram_thread_id != task.telegram_thread_id:
            return CallbackAnswerRead(
                task_id=task_id,
                task_status=task.status,
                task_external_id=task.external_id,
                action_valid=False,
                action=action,
                error="Thread mismatch",
            )

    # 4. Resolve approval. Compact callbacks never carry approval UUIDs, so
    # approve/reject resolve the current pending approval for the task.
    approval_id: UUID | None = None
    approval_status: str | None = None
    try:
        approval_uuid_raw = fields.get("approval_id", "")
        if approval_uuid_raw and approval_uuid_raw != "none":
            approval_id = UUID(approval_uuid_raw)
    except (ValueError, TypeError):
        pass

    if approval_id is not None:
        approval = await asvc.get(approval_id)
        if approval is not None:
            approval_status = approval.status
            if str(approval.task_id) != str(task_id):
                return CallbackAnswerRead(
                    task_id=task_id,
                    task_status=task.status,
                    task_external_id=task.external_id,
                    approval_id=approval_id,
                    approval_status=approval_status,
                    action_valid=False,
                    action=action,
                    error="Approval task mismatch",
                )

    if fields.get("protocol") == "compact" and action in {"approve", "reject"}:
        pending_approvals = [
            approval
            for approval in await asvc.list_by_task(task_id)
            if approval.status == ApprovalStatus.PENDING.value
        ]
        if not pending_approvals:
            return CallbackAnswerRead(
                task_id=task_id,
                task_status=task.status,
                task_external_id=task.external_id,
                action_valid=False,
                action=action,
                error="No pending approval for task",
            )
        approval = pending_approvals[0]
        approval_id = approval.id
        approval_status = approval.status

    # 5. SEC-01: if action is approve/reject and telegram_user_id is provided,
    #    verify the user has admin permission.
    if action in {"approve", "reject"} and body.telegram_user_id is not None:
        perm_action = PermissionAction.APPROVE if action == "approve" else PermissionAction.REJECT
        engine = _engine()
        ctx = context_for_callback(
            user_id=body.telegram_user_id,
            action=perm_action,
            task_id=str(task_id),
            project_id=str(task.project_id) if task.project_id else None,
            agent_id=str(task.agent_id) if task.agent_id else None,
            risk_level=task.risk_level,
        )
        decision = engine.evaluate(ctx)
        if not decision.allowed:
            raise HTTPException(status_code=403, detail=decision.reason)

    # 6. Audit event
    await esvc.create(
        task_id,
        "callback_received",
        ActorType.USER if body.telegram_user_id else ActorType.SYSTEM,
        actor_id=str(body.telegram_user_id) if body.telegram_user_id else None,
        payload={"action": action},
    )

    return CallbackAnswerRead(
        task_id=task_id,
        task_status=task.status,
        task_external_id=task.external_id,
        approval_id=approval_id,
        approval_status=approval_status,
        action_valid=True,
        action=action,
    )
