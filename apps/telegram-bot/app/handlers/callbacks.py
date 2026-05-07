"""TG-03: Inline keyboard callback handler for task/approval actions.

Handles callback_data actions: approve, reject, show_plan, show_task, refresh.
Sends callback_answer to API for validation, then performs the action.
"""

from __future__ import annotations

from uuid import UUID

from aiogram import Router
from aiogram.types import CallbackQuery

from app.keyboards import build_plan_keyboard, build_task_keyboard
from app.services import get_api_client
from app.services.formatters import (
    format_error_message,
    format_plan_excerpt,
    format_task_card,
)

router = Router(name="callbacks")


def _extract_task_id_from_cb(callback_data: str) -> str | None:
    """Extract task UUID (legacy) or task external_id (compact) from callback data."""
    if callback_data.startswith("v1:"):
        parts = callback_data.split(":")
        if len(parts) == 5 and parts[2].startswith("task-"):
            return parts[2]
        return None

    parts = callback_data.split("|")
    if len(parts) >= 3:
        try:
            UUID(parts[2])
            return parts[2]
        except (ValueError, TypeError):
            return None
    return None


async def _resolve_task_uuid_for_callback(client, task_ref: str) -> str | None:
    """Resolve compact external_id to API UUID; legacy UUIDs pass through unchanged."""
    try:
        UUID(task_ref)
        return task_ref
    except (ValueError, TypeError):
        pass

    if not task_ref.startswith("task-"):
        return None
    task = await client.find_task_by_external_id(task_ref)
    if not task:
        return None
    task_id = task.get("id")
    if not isinstance(task_id, str):
        return None
    try:
        UUID(task_id)
    except (ValueError, TypeError):
        return None
    return task_id


async def _get_chat_thread_ids(query: CallbackQuery) -> tuple[int | None, int | None, int | None]:
    """Extract chat_id, thread_id, user_id from callback query."""
    chat_id = None
    thread_id = None
    user_id = None
    if query.message:
        chat_id = query.message.chat.id
        thread_id = query.message.message_thread_id
    if query.from_user:
        user_id = query.from_user.id
    return chat_id, thread_id, user_id


@router.callback_query()
async def handle_callback(query: CallbackQuery) -> None:
    """Process all inline button callbacks."""
    callback_data = query.data or ""
    if not callback_data:
        await query.answer("No callback data", show_alert=False)
        return

    # Extract task_id early
    task_ref = _extract_task_id_from_cb(callback_data)
    if not task_ref:
        await query.answer("Invalid callback data", show_alert=False)
        return

    chat_id, thread_id, user_id = await _get_chat_thread_ids(query)

    client = get_api_client()

    try:
        task_id = await _resolve_task_uuid_for_callback(client, task_ref)
    except Exception as exc:
        await query.answer(f"API error: {exc}", show_alert=True)
        return
    if not task_id:
        await query.answer("Task not found", show_alert=True)
        return

    # Step 1: Validate callback via API
    try:
        cb_body = {
            "callback_data": callback_data,
        }
        if chat_id is not None:
            cb_body["telegram_chat_id"] = chat_id
        if thread_id is not None:
            cb_body["telegram_thread_id"] = thread_id
        if user_id is not None:
            cb_body["telegram_user_id"] = user_id

        cb_result = await client.callback_answer(task_id, cb_body)
    except Exception as exc:
        await query.answer(f"API error: {exc}", show_alert=True)
        return

    if not cb_result.get("action_valid"):
        error_text = cb_result.get("error", "Unknown validation error")
        await query.answer(format_error_message("Callback rejected", error_text)[:200], show_alert=True)
        return

    action = cb_result.get("action", "unknown")
    keyboard_task_ref = cb_result.get("task_external_id") or task_ref

    # Step 2: Perform the action
    if action == "approve":
        await _handle_approve_action(query, client, task_id, cb_result)
    elif action == "reject":
        await _handle_reject_action(query, client, task_id, cb_result)
    elif action == "show_plan":
        await _handle_show_plan_action(query, client, task_id, keyboard_task_ref)
    elif action == "show_task":
        await _handle_show_task_action(query, client, task_id)
    elif action == "refresh":
        await _handle_refresh_action(query, client, task_id)
    else:
        await query.answer(f"Unknown action: {action}", show_alert=False)


async def _handle_approve_action(
    query: CallbackQuery,
    client,
    task_id: str,
    cb_result: dict,
) -> None:
    """Handle approve button click — call API to approve, then show updated card."""
    approval_id = cb_result.get("approval_id")
    if not approval_id:
        await query.answer("No pending approval to act on", show_alert=True)
        return

    try:
        user_id = query.from_user.id if query.from_user else None
        await client.approve_approval(approval_id, {"approved_by": user_id})
        await query.answer("Approved!", show_alert=False)
    except Exception as exc:
        await query.answer(f"Approve failed: {exc}", show_alert=True)
        return

    # Refresh the message with updated state
    await _refresh_message(query, client, task_id)


async def _handle_reject_action(
    query: CallbackQuery,
    client,
    task_id: str,
    cb_result: dict,
) -> None:
    """Handle reject button click — call API to reject, then show updated card."""
    approval_id = cb_result.get("approval_id")
    if not approval_id:
        await query.answer("No pending approval to act on", show_alert=True)
        return

    try:
        user_id = query.from_user.id if query.from_user else None
        await client.reject_approval(
            approval_id,
            {"approved_by": user_id, "reason": "Rejected via Telegram inline button"},
        )
        await query.answer("Rejected.", show_alert=False)
    except Exception as exc:
        await query.answer(f"Reject failed: {exc}", show_alert=True)
        return

    # Refresh the message with updated state
    await _refresh_message(query, client, task_id)


async def _handle_show_plan_action(
    query: CallbackQuery,
    client,
    task_id: str,
    keyboard_task_ref: str,
) -> None:
    """Handle show plan button — fetch and display plan text."""
    try:
        plan_data = await client.get_task_plan(task_id)
    except Exception as exc:
        await query.answer(f"Failed to fetch plan: {exc}", show_alert=True)
        return

    plan_text = plan_data.get("plan_text")
    task_status = plan_data.get("status", "unknown")
    try:
        UUID(keyboard_task_ref)
        task = await client.get_task(task_id)
        keyboard_task_ref = task.get("external_id") or keyboard_task_ref
    except Exception:
        pass

    excerpt = format_plan_excerpt(plan_text)
    header = f"📋 <b>Plan — Task {task_id[:8]}</b>\nStatus: <code>{task_status}</code>\n\n"
    text = header + excerpt

    try:
        keyboard = build_plan_keyboard(keyboard_task_ref)
    except ValueError:
        keyboard = None

    try:
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception:
        # If edit fails (e.g., same content), just answer
        pass

    await query.answer()


async def _handle_show_task_action(
    query: CallbackQuery,
    client,
    task_id: str,
) -> None:
    """Handle show task button — fetch and display task card."""
    await _refresh_message(query, client, task_id)


async def _handle_refresh_action(
    query: CallbackQuery,
    client,
    task_id: str,
) -> None:
    """Handle refresh button — re-fetch task and update the message."""
    await _refresh_message(query, client, task_id)


async def _refresh_message(query: CallbackQuery, client, task_id: str) -> None:
    """Fetch latest task state and update the original message."""
    try:
        task = await client.get_task(task_id)
    except Exception as exc:
        await query.answer(f"Failed to refresh: {exc}", show_alert=True)
        return

    # Check for pending approvals
    has_pending = False
    approval_id = None
    has_plan = bool(task.get("plan_text"))

    try:
        approvals = await client.list_approvals_by_task(task_id)
        for a in approvals:
            if a.get("status") == "pending":
                has_pending = True
                approval_id = a.get("id")
                break
    except Exception:
        pass

    text = format_task_card(task)
    keyboard_task_ref = task.get("external_id") or task_id
    keyboard = build_task_keyboard(
        task_id=keyboard_task_ref,
        task_status=task.get("status", ""),
        has_pending_approval=has_pending,
        approval_id=approval_id,
        has_plan=has_plan,
    )

    try:
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception:
        # If same content, just answer silently
        pass

    await query.answer("Refreshed ✓", show_alert=False)
