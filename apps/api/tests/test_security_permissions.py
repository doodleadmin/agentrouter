"""Unit tests for PermissionEngine (no DB, no HTTP) — SEC-01 Phase 2."""

import pytest

from app.db.enums import ActorType, RiskLevel
from app.security.context import context_for_telegram_user
from app.security.permissions import PermissionAction, PermissionContext, PermissionEngine

TEST_ADMIN_ID = "1113930428"


class TestPermissionEngine:
    """PermissionEngine unit tests — isolated from DB and HTTP."""

    # ── approve ────────────────────────────────────────────────────────

    def test_can_approve_admin_allowed(self) -> None:
        engine = PermissionEngine(admin_user_ids=[TEST_ADMIN_ID])
        ctx = context_for_telegram_user(TEST_ADMIN_ID, PermissionAction.APPROVE, task_id="task-1")
        decision = engine.can_approve(ctx)
        assert decision.allowed is True

    def test_can_approve_non_admin_denied(self) -> None:
        engine = PermissionEngine(admin_user_ids=[TEST_ADMIN_ID])
        ctx = context_for_telegram_user("999999999", PermissionAction.APPROVE, task_id="task-1")
        decision = engine.can_approve(ctx)
        assert decision.allowed is False
        assert "admin" in decision.reason.lower()

    def test_can_approve_no_actor_denied(self) -> None:
        engine = PermissionEngine(admin_user_ids=[TEST_ADMIN_ID])
        ctx = PermissionContext(actor_type=ActorType.USER, action=PermissionAction.APPROVE, task_id="task-1")
        decision = engine.can_approve(ctx)
        assert decision.allowed is False

    # ── reject ─────────────────────────────────────────────────────────

    def test_can_reject_admin_allowed(self) -> None:
        engine = PermissionEngine(admin_user_ids=[TEST_ADMIN_ID])
        ctx = context_for_telegram_user(TEST_ADMIN_ID, PermissionAction.REJECT, task_id="task-1")
        decision = engine.can_reject(ctx)
        assert decision.allowed is True

    def test_can_reject_non_admin_denied(self) -> None:
        engine = PermissionEngine(admin_user_ids=[TEST_ADMIN_ID])
        ctx = context_for_telegram_user("999999999", PermissionAction.REJECT, task_id="task-1")
        decision = engine.can_reject(ctx)
        assert decision.allowed is False
        assert "admin" in decision.reason.lower()

    # ── empty admin list (fail-closed) ─────────────────────────────────

    def test_approve_admin_list_empty_denies(self) -> None:
        engine = PermissionEngine(admin_user_ids=[])
        ctx = context_for_telegram_user(TEST_ADMIN_ID, PermissionAction.APPROVE, task_id="task-1")
        decision = engine.can_approve(ctx)
        assert decision.allowed is False
        assert "empty" in decision.reason.lower()

    def test_reject_admin_list_empty_denies(self) -> None:
        engine = PermissionEngine(admin_user_ids=[])
        ctx = context_for_telegram_user(TEST_ADMIN_ID, PermissionAction.REJECT, task_id="task-1")
        decision = engine.can_reject(ctx)
        assert decision.allowed is False
        assert "empty" in decision.reason.lower()

    # ── trigger_plan — risk-level gating ────────────────────────────────

    def test_trigger_plan_low_risk_allowed(self) -> None:
        engine = PermissionEngine(admin_user_ids=[TEST_ADMIN_ID])
        ctx = PermissionContext(
            actor_type=ActorType.USER,
            actor_id=TEST_ADMIN_ID,
            action=PermissionAction.TRIGGER_PLAN,
            task_id="t1",
            project_id="p1",
            agent_id="a1",
            risk_level=RiskLevel.LOW,
        )
        decision = engine.can_trigger_plan(ctx)
        assert decision.allowed is True
        assert decision.requires_approval is False

    def test_trigger_plan_medium_risk_requires_approval(self) -> None:
        engine = PermissionEngine(admin_user_ids=[TEST_ADMIN_ID])
        ctx = PermissionContext(
            actor_type=ActorType.USER,
            actor_id=TEST_ADMIN_ID,
            action=PermissionAction.TRIGGER_PLAN,
            task_id="t1",
            project_id="p1",
            agent_id="a1",
            risk_level=RiskLevel.MEDIUM,
        )
        decision = engine.can_trigger_plan(ctx)
        assert decision.allowed is True
        assert decision.requires_approval is True

    def test_trigger_plan_high_risk_denied(self) -> None:
        engine = PermissionEngine(admin_user_ids=[TEST_ADMIN_ID])
        ctx = PermissionContext(
            actor_type=ActorType.USER,
            actor_id=TEST_ADMIN_ID,
            action=PermissionAction.TRIGGER_PLAN,
            task_id="t1",
            project_id="p1",
            agent_id="a1",
            risk_level=RiskLevel.HIGH,
        )
        decision = engine.can_trigger_plan(ctx)
        assert decision.allowed is False

    def test_trigger_plan_critical_risk_denied(self) -> None:
        engine = PermissionEngine(admin_user_ids=[TEST_ADMIN_ID])
        ctx = PermissionContext(
            actor_type=ActorType.USER,
            actor_id=TEST_ADMIN_ID,
            action=PermissionAction.TRIGGER_PLAN,
            task_id="t1",
            project_id="p1",
            agent_id="a1",
            risk_level=RiskLevel.CRITICAL,
        )
        decision = engine.can_trigger_plan(ctx)
        assert decision.allowed is False

    def test_trigger_plan_missing_context_denied(self) -> None:
        engine = PermissionEngine(admin_user_ids=[TEST_ADMIN_ID])
        ctx = PermissionContext(
            actor_type=ActorType.USER,
            action=PermissionAction.TRIGGER_PLAN,
            task_id="t1",
            # project_id and agent_id missing
        )
        decision = engine.can_trigger_plan(ctx)
        assert decision.allowed is False

    # ── update_status ──────────────────────────────────────────────────

    def test_update_status_system_allowed(self) -> None:
        engine = PermissionEngine(admin_user_ids=[])
        ctx = PermissionContext(
            actor_type=ActorType.SYSTEM,
            action=PermissionAction.UPDATE_STATUS,
            task_id="t1",
        )
        decision = engine.can_update_status(ctx)
        assert decision.allowed is True

    def test_update_status_agent_denied(self) -> None:
        engine = PermissionEngine(admin_user_ids=[TEST_ADMIN_ID])
        ctx = PermissionContext(
            actor_type=ActorType.AGENT,
            action=PermissionAction.UPDATE_STATUS,
            task_id="t1",
        )
        decision = engine.can_update_status(ctx)
        assert decision.allowed is False

    # ── unknown action ─────────────────────────────────────────────────

    def test_unknown_action_denied(self) -> None:
        engine = PermissionEngine(admin_user_ids=[TEST_ADMIN_ID])
        ctx = PermissionContext(
            actor_type=ActorType.USER,
            actor_id=TEST_ADMIN_ID,
            action=PermissionAction.DANGEROUS_TOOL,
        )
        decision = engine.evaluate(ctx)
        assert decision.allowed is False

    # ── deny reason security ───────────────────────────────────────────

    def test_deny_reason_no_secrets(self) -> None:
        """All deny reasons must be secret-free — no admin IDs leaked."""
        engine = PermissionEngine(admin_user_ids=[TEST_ADMIN_ID])
        ctx = context_for_telegram_user("999999999", PermissionAction.APPROVE, task_id="t1")
        decision = engine.can_approve(ctx)
        assert TEST_ADMIN_ID not in decision.reason  # admin IDs not leaked
        assert "token" not in decision.reason.lower()
        assert "secret" not in decision.reason.lower()
        assert "password" not in decision.reason.lower()

    # ── determinism ────────────────────────────────────────────────────

    def test_deterministic_decision(self) -> None:
        engine = PermissionEngine(admin_user_ids=[TEST_ADMIN_ID])
        ctx = context_for_telegram_user(TEST_ADMIN_ID, PermissionAction.APPROVE, task_id="t1")
        d1 = engine.can_approve(ctx)
        d2 = engine.can_approve(ctx)
        assert d1.allowed == d2.allowed

    # ── context serialization ──────────────────────────────────────────

    def test_context_serialization(self) -> None:
        ctx = context_for_telegram_user(TEST_ADMIN_ID, PermissionAction.APPROVE, task_id="t1")
        data = ctx.model_dump()
        assert data["actor_type"] == "user"
        assert data["actor_id"] == TEST_ADMIN_ID
        assert data["action"] == "approve"

    # ── stubs ──────────────────────────────────────────────────────────

    def test_stubs_allowed(self) -> None:
        engine = PermissionEngine(admin_user_ids=[])
        for action in [
            PermissionAction.CREATE_TASK,
            PermissionAction.EXECUTE_RUNTIME,
            PermissionAction.ACCESS_PROJECT,
            PermissionAction.WRITE_MEMORY,
        ]:
            ctx = PermissionContext(actor_type=ActorType.SYSTEM, action=action)
            decision = engine.evaluate(ctx)
            assert decision.allowed is True, f"Stub {action} should be allowed"

    # ── evaluate dispatches correctly ──────────────────────────────────

    def test_evaluate_no_action_denied(self) -> None:
        engine = PermissionEngine(admin_user_ids=[TEST_ADMIN_ID])
        ctx = PermissionContext(actor_type=ActorType.USER, action=None)
        decision = engine.evaluate(ctx)
        assert decision.allowed is False
        assert decision.audit_code == "SEC-PERM-NO-ACTION"
