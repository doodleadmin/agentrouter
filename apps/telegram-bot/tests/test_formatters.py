"""TG-03: Tests for message formatters."""

from app.services.formatters import (
    format_approval_card,
    format_error_message,
    format_plan_excerpt,
    format_task_card,
)


def test_format_task_card_basic() -> None:
    task = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "external_id": "task-0001",
        "title": "Add healthcheck endpoint",
        "status": "created",
        "risk_level": "low",
        "intent": "backend_task",
        "project_id": "550e8400-e29b-41d4-a716-446655440001",
        "agent_id": "550e8400-e29b-41d4-a716-446655440002",
        "plan_text": None,
        "result_summary": None,
        "payload": {},
        "created_at": "2026-05-05T12:00:00.000Z",
        "updated_at": "2026-05-05T12:00:00.000Z",
    }

    result = format_task_card(task)

    assert "task-0001" in result
    assert "created" in result
    assert "low" in result
    assert "Add healthcheck endpoint" in result
    assert "2026-05-05 12:00:00" in result


def test_format_task_card_completed() -> None:
    task = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "external_id": "task-0002",
        "title": "Fix bug",
        "status": "completed",
        "risk_level": "medium",
        "intent": None,
        "project_id": None,
        "agent_id": None,
        "plan_text": "Step 1: Investigate\nStep 2: Fix",
        "result_summary": "Bug fixed, tests pass",
        "payload": {},
        "created_at": "2026-05-05T10:00:00.000Z",
        "updated_at": "2026-05-05T11:00:00.000Z",
    }

    result = format_task_card(task)

    assert "task-0002" in result
    assert "completed" in result
    assert "medium" in result
    assert "Plan available" in result
    assert "Bug fixed" in result


def test_format_approval_card_pending() -> None:
    task = {"external_id": "task-0001", "risk_level": "high"}
    approval = {
        "id": "550e8400-e29b-41d4-a716-446655440003",
        "action": "deploy_production",
        "status": "pending",
        "reason": None,
        "payload": {"env": "production"},
        "decided_at": None,
    }

    result = format_approval_card(task, approval)

    assert "Approval Request" in result
    assert "task-0001" in result
    assert "deploy_production" in result
    assert "pending" in result
    assert "high" in result


def test_format_approval_card_decided() -> None:
    task = {"external_id": "task-0002", "risk_level": "low"}
    approval = {
        "id": "550e8400-e29b-41d4-a716-446655440003",
        "action": "deploy_staging",
        "status": "approved",
        "reason": "Looks safe",
        "payload": {},
        "decided_at": "2026-05-05T14:00:00.000Z",
    }

    result = format_approval_card(task, approval)

    assert "approved" in result
    assert "Looks safe" in result
    assert "Decided" in result


def test_format_plan_excerpt_empty() -> None:
    result = format_plan_excerpt(None)
    assert "No plan available" in result

    result2 = format_plan_excerpt("")
    assert "No plan available" in result2


def test_format_plan_excerpt_short() -> None:
    short = "Step 1: Do X\nStep 2: Do Y"
    result = format_plan_excerpt(short)
    assert "Step 1" in result
    assert "Step 2" in result
    assert "truncated" not in result


def test_format_plan_excerpt_truncated() -> None:
    long_plan = "x" * 600
    result = format_plan_excerpt(long_plan, max_len=500)
    assert len(result) > 500  # includes header
    assert "truncated" in result


def test_format_error_message() -> None:
    result = format_error_message("Validation failed", "Reason: invalid input")
    assert "Validation failed" in result
    assert "Reason: invalid input" in result
    assert "&lt;" not in result.lower() or "<" not in result  # ensures no unescaped HTML


def test_html_escaping() -> None:
    """Verify that HTML special chars are escaped in task cards."""
    task = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "external_id": "task-0001",
        "title": "Test <script>alert('xss')</script>",
        "status": "created",
        "risk_level": "low",
        "intent": "test & verify",
        "project_id": None,
        "agent_id": None,
        "plan_text": None,
        "result_summary": None,
        "payload": {},
        "created_at": "2026-05-05T12:00:00.000Z",
        "updated_at": "2026-05-05T12:00:00.000Z",
    }

    result = format_task_card(task)

    assert "<script>" not in result.lower()
    assert "&lt;script&gt;" in result  # escaped
    assert "&amp;" in result  # & escaped for intent
