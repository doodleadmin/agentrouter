"""TG-06: Tests for compact Telegram callback keyboard protocol."""

from app import keyboards


def _callback_data(markup) -> list[str]:
    return [button.callback_data for row in markup.inline_keyboard for button in row]


def test_task_keyboard_uses_compact_callbacks_without_uuid_or_approval_or_reason(monkeypatch) -> None:
    monkeypatch.setattr(keyboards, "_get_callback_secret", lambda: "test-secret")
    markup = keyboards.build_task_keyboard(
        task_id="task-0004",
        task_status="waiting_approval",
        has_pending_approval=True,
        approval_id="550e8400-e29b-41d4-a716-446655440000",
        has_plan=True,
    )

    callbacks = _callback_data(markup)
    assert len(callbacks) == 4
    assert {cb.split(":")[1] for cb in callbacks} == {"a", "r", "p", "f"}
    for cb in callbacks:
        assert len(cb.encode("utf-8")) <= 64
        assert cb.startswith("v1:")
        assert "550e8400-e29b-41d4-a716-446655440000" not in cb
        assert "Rejected via" not in cb
        assert ":task-0004:" in cb


def test_plan_keyboard_uses_compact_show_task_and_refresh(monkeypatch) -> None:
    monkeypatch.setattr(keyboards, "_get_callback_secret", lambda: "test-secret")
    markup = keyboards.build_plan_keyboard("task-0004")

    callbacks = _callback_data(markup)
    assert len(callbacks) == 2
    assert {cb.split(":")[1] for cb in callbacks} == {"t", "f"}
    for cb in callbacks:
        assert len(cb.encode("utf-8")) <= 64
        assert ":task-0004:" in cb


def test_approval_keyboard_uses_compact_approve_reject_refresh(monkeypatch) -> None:
    monkeypatch.setattr(keyboards, "_get_callback_secret", lambda: "test-secret")
    approval_id = "550e8400-e29b-41d4-a716-446655440000"
    markup = keyboards.build_approval_keyboard("task-0004", approval_id)

    callbacks = _callback_data(markup)
    assert {cb.split(":")[1] for cb in callbacks} == {"a", "r", "f"}
    for cb in callbacks:
        assert len(cb.encode("utf-8")) <= 64
        assert approval_id not in cb
        assert ":task-0004:" in cb
