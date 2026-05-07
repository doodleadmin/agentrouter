"""Permission Engine — centralized authorization for SEC-01 Phase 2.

Fail-closed design: unknown actions and empty admin lists always deny.
"""

from enum import StrEnum

from pydantic import BaseModel, Field

from app.db.enums import ActorType, RiskLevel


class PermissionAction(StrEnum):
    """All actions that can be checked by the PermissionEngine."""

    CREATE_TASK = "create_task"
    TRIGGER_PLAN = "trigger_plan"
    APPROVE = "approve"
    REJECT = "reject"
    CANCEL_TASK = "cancel_task"
    UPDATE_STATUS = "update_status"
    EXECUTE_RUNTIME = "execute_runtime"
    ACCESS_PROJECT = "access_project"
    MODIFY_PROJECT = "modify_project"
    MODIFY_AGENT = "modify_agent"
    WRITE_MEMORY = "write_memory"
    CALLBACK_VALIDATE = "callback_validate"
    DANGEROUS_TOOL = "dangerous_tool"


class PermissionDecision(BaseModel):
    """Result of a permission check.

    Attributes:
        allowed: Whether the action is permitted.
        reason: Human-readable explanation (never contains secrets).
        requires_approval: If True, the action needs explicit admin approval.
        audit_code: Machine-readable code for audit logging.
    """

    allowed: bool = False
    reason: str = ""
    requires_approval: bool = False
    audit_code: str = ""


class PermissionContext(BaseModel):
    """All information needed to evaluate a permission check.

    Attributes:
        actor_type: Who is performing the action (user, agent, system).
        actor_id: Telegram user ID or agent slug (None for system).
        actor_role: Agent role slug (for agent actors).
        source: Origin of the request (telegram, api, worker, system).
        project_id: Target project UUID string.
        agent_id: Target agent UUID string.
        task_id: Target task UUID string.
        risk_level: Task risk level (for risk-gated actions).
        action: The action being checked.
        metadata: Additional context (arbitrary key-value pairs).
    """

    actor_type: ActorType
    actor_id: str | None = None
    actor_role: str | None = None
    source: str | None = None  # "telegram", "api", "worker", "system"
    project_id: str | None = None
    agent_id: str | None = None
    task_id: str | None = None
    risk_level: RiskLevel | None = None
    action: PermissionAction | None = None
    metadata: dict = Field(default_factory=dict)


class PermissionEngine:
    """Centralized permission engine — fail-closed design.

    Constructor takes admin_user_ids: list of Telegram user IDs that have
    admin privileges. An empty list means all admin-gated actions are denied
    (fail-closed).
    """

    def __init__(self, admin_user_ids: list[str]) -> None:
        self._admin_ids: set[str] = set(admin_user_ids)

    # ── public entry point ──────────────────────────────────────────────

    def evaluate(self, ctx: PermissionContext) -> PermissionDecision:
        """Dispatch to the appropriate can_* method based on action."""
        action = ctx.action
        if action is None:
            return PermissionDecision(
                allowed=False,
                reason="no action specified",
                audit_code="SEC-PERM-NO-ACTION",
            )

        dispatch: dict[PermissionAction, callable] = {
            PermissionAction.APPROVE: self.can_approve,
            PermissionAction.REJECT: self.can_reject,
            PermissionAction.TRIGGER_PLAN: self.can_trigger_plan,
            PermissionAction.UPDATE_STATUS: self.can_update_status,
            PermissionAction.CREATE_TASK: self.can_create_task,
            PermissionAction.EXECUTE_RUNTIME: self.can_execute_runtime,
            PermissionAction.ACCESS_PROJECT: self.can_access_project,
            PermissionAction.WRITE_MEMORY: self.can_write_memory,
            PermissionAction.CANCEL_TASK: self.can_cancel_task,
            PermissionAction.CALLBACK_VALIDATE: self.can_callback_validate,
            PermissionAction.MODIFY_PROJECT: self.can_modify_project,
            PermissionAction.MODIFY_AGENT: self.can_modify_agent,
            PermissionAction.DANGEROUS_TOOL: self.can_dangerous_tool,
        }

        handler = dispatch.get(action)
        if handler is None:
            return PermissionDecision(
                allowed=False,
                reason="unknown action",
                audit_code="SEC-PERM-UNKNOWN",
            )
        return handler(ctx)

    # ── admin-gated actions ─────────────────────────────────────────────

    def can_approve(self, ctx: PermissionContext) -> PermissionDecision:
        """Approve — requires admin role (actor_id in admin list)."""
        return self._check_admin_gated(
            ctx,
            deny_reason="approval requires admin role",
            allow_code="SEC-PERM-APPROVE-ALLOW",
            deny_code="SEC-PERM-APPROVE-DENY",
        )

    def can_reject(self, ctx: PermissionContext) -> PermissionDecision:
        """Reject — requires admin role (actor_id in admin list)."""
        return self._check_admin_gated(
            ctx,
            deny_reason="rejection requires admin role",
            allow_code="SEC-PERM-REJECT-ALLOW",
            deny_code="SEC-PERM-REJECT-DENY",
        )

    # ── risk-gated action ───────────────────────────────────────────────

    def can_trigger_plan(self, ctx: PermissionContext) -> PermissionDecision:
        """Trigger plan — risk-level-based gating.

        - LOW: allowed immediately
        - MEDIUM: allowed but requires_approval=True
        - HIGH/CRITICAL: denied (requires admin)
        """
        if not ctx.task_id or not ctx.project_id or not ctx.agent_id:
            return PermissionDecision(
                allowed=False,
                reason="incomplete task context",
                audit_code="SEC-PERM-TRIGGER-INC",
            )

        risk = ctx.risk_level
        if risk is None:
            risk = RiskLevel.LOW

        if risk == RiskLevel.LOW:
            return PermissionDecision(
                allowed=True,
                reason="low-risk task — planning allowed",
                requires_approval=False,
                audit_code="SEC-PERM-TRIGGER-LOW",
            )
        elif risk == RiskLevel.MEDIUM:
            return PermissionDecision(
                allowed=True,
                reason="medium-risk task requires approval before execution",
                requires_approval=True,
                audit_code="SEC-PERM-TRIGGER-MED",
            )
        elif risk == RiskLevel.HIGH:
            return PermissionDecision(
                allowed=False,
                reason="high-risk tasks require admin approval",
                audit_code="SEC-PERM-TRIGGER-HIGH",
            )
        elif risk == RiskLevel.CRITICAL:
            return PermissionDecision(
                allowed=False,
                reason="critical-risk tasks require admin approval",
                audit_code="SEC-PERM-TRIGGER-CRIT",
            )
        else:
            return PermissionDecision(
                allowed=False,
                reason="unknown risk level",
                audit_code="SEC-PERM-TRIGGER-UNK",
            )

    # ── status update ───────────────────────────────────────────────────

    def can_update_status(self, ctx: PermissionContext) -> PermissionDecision:
        """Update task status — system actors always allowed, users need approval."""
        if ctx.actor_type == ActorType.SYSTEM:
            return PermissionDecision(
                allowed=True,
                reason="system actor",
                audit_code="SEC-PERM-STATUS-ALLOW",
            )
        if ctx.actor_type == ActorType.USER:
            return PermissionDecision(
                allowed=True,
                reason="user-initiated status update — approval flag set",
                requires_approval=True,
                audit_code="SEC-PERM-STATUS-ALLOW",
            )
        return PermissionDecision(
            allowed=False,
            reason="status update requires system actor or admin approval",
            audit_code="SEC-PERM-STATUS-DENY",
        )

    # ── stubs (deferred to Phase 3) ─────────────────────────────────────

    def can_execute_runtime(self, ctx: PermissionContext) -> PermissionDecision:
        """Stub — agent permissions deferred to SEC-01 Phase 3."""
        return PermissionDecision(
            allowed=True,
            reason="stub — agent permissions deferred to Phase 3",
            audit_code="SEC-PERM-RUNTIME-STUB",
        )

    def can_create_task(self, ctx: PermissionContext) -> PermissionDecision:
        """Stub — task creation deferred to SEC-01 Phase 3."""
        return PermissionDecision(
            allowed=True,
            reason="stub — task creation deferred to Phase 3",
            audit_code="SEC-PERM-CREATE-STUB",
        )

    def can_access_project(self, ctx: PermissionContext) -> PermissionDecision:
        """Stub — project access deferred to SEC-01 Phase 3."""
        return PermissionDecision(
            allowed=True,
            reason="stub — project access deferred to Phase 3",
            audit_code="SEC-PERM-PROJECT-STUB",
        )

    def can_write_memory(self, ctx: PermissionContext) -> PermissionDecision:
        """Stub — memory write tier deferred to SEC-01 Phase 3."""
        return PermissionDecision(
            allowed=True,
            reason="stub — memory write tier deferred to Phase 3",
            audit_code="SEC-PERM-MEMORY-STUB",
        )

    # ── other stubs ─────────────────────────────────────────────────────

    def can_cancel_task(self, ctx: PermissionContext) -> PermissionDecision:
        """Stub — cancel task deferred to SEC-01 Phase 3."""
        return PermissionDecision(
            allowed=True,
            reason="stub — cancel task deferred to Phase 3",
            audit_code="SEC-PERM-CANCEL-STUB",
        )

    def can_callback_validate(self, ctx: PermissionContext) -> PermissionDecision:
        """Stub — callback validation deferred to SEC-01 Phase 3."""
        return PermissionDecision(
            allowed=True,
            reason="stub — callback validation deferred to Phase 3",
            audit_code="SEC-PERM-CALLBACK-STUB",
        )

    def can_modify_project(self, ctx: PermissionContext) -> PermissionDecision:
        """Stub — modify project deferred to SEC-01 Phase 3."""
        return PermissionDecision(
            allowed=True,
            reason="stub — modify project deferred to Phase 3",
            audit_code="SEC-PERM-MODPROJ-STUB",
        )

    def can_modify_agent(self, ctx: PermissionContext) -> PermissionDecision:
        """Stub — modify agent deferred to SEC-01 Phase 3."""
        return PermissionDecision(
            allowed=True,
            reason="stub — modify agent deferred to Phase 3",
            audit_code="SEC-PERM-MODAGNT-STUB",
        )

    def can_dangerous_tool(self, ctx: PermissionContext) -> PermissionDecision:
        """Dangerous tool — always denied in Phase 2."""
        return PermissionDecision(
            allowed=False,
            reason="dangerous tool usage requires admin approval",
            audit_code="SEC-PERM-DANGER-DENY",
        )

    # ── internal helpers ────────────────────────────────────────────────

    def _check_admin_gated(
        self,
        ctx: PermissionContext,
        deny_reason: str,
        allow_code: str,
        deny_code: str,
    ) -> PermissionDecision:
        """Shared logic for admin-gated actions (approve, reject).

        Rules:
        - ALLOW if actor_id in admin_user_ids AND admin list non-empty.
        - DENY if actor_id is None.
        - DENY if actor_id not in admin list.
        - DENY if admin list is empty (fail-closed).
        - NEVER include admin IDs or secrets in reason.
        """
        # Fail-closed: empty admin list denies everyone
        if not self._admin_ids:
            return PermissionDecision(
                allowed=False,
                reason="admin list is empty, fail-closed",
                audit_code=deny_code,
            )

        if ctx.actor_id is None:
            return PermissionDecision(
                allowed=False,
                reason=deny_reason,
                audit_code=deny_code,
            )

        if ctx.actor_id in self._admin_ids:
            return PermissionDecision(
                allowed=True,
                reason="admin authorized",
                audit_code=allow_code,
            )

        return PermissionDecision(
            allowed=False,
            reason=deny_reason,
            audit_code=deny_code,
        )
