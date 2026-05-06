"""TG-03: /approve <task_id|external_id> — approve the latest pending approval for a task.
TG-05: Admin gate — only TELEGRAM_ADMIN_USER_IDS can approve."""

from html import escape as html_escape

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import settings
from app.keyboards import build_task_keyboard
from app.services import get_api_client
from app.services.formatters import format_error_message, format_task_card

router = Router(name="approve")


@router.message(Command("approve"))
async def approve_handler(message: Message) -> None:
    # ── TG-05: Admin gate (fail-closed) ────────────────────────────────
    if message.from_user is None:
        await message.answer("⛔ Не удалось определить пользователя.")
        return

    user_id = message.from_user.id
    admin_ids = settings.admin_user_ids()

    if not admin_ids or user_id not in admin_ids:
        await message.answer("⛔ Только администраторы могут подтверждать задачи.")
        return

    client = get_api_client()
    args = (message.text or "").strip().split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ Usage: /approve <code>task_id</code> or <code>external_id</code>")
        return

    task_ref = args[1].strip()

    # Resolve task
    task = None
    try:
        task = await client.get_task(task_ref)
    except Exception:
        pass

    if task is None:
        try:
            task = await client.find_task_by_external_id(task_ref)
        except Exception:
            pass

    if task is None:
        await message.answer(
            format_error_message("Task not found", f"No task matching '{task_ref}'"),
        )
        return

    task_id = task["id"]

    # Find pending approval
    try:
        approvals = await client.list_approvals_by_task(task_id)
    except Exception as exc:
        await message.answer(format_error_message("API error", str(exc)))
        return

    pending = [a for a in approvals if a.get("status") == "pending"]
    if not pending:
        await message.answer("ℹ️ No pending approvals for this task.")
        # Still show task status
        text = format_task_card(task)
        await message.answer(text, parse_mode="HTML")
        return

    # Approve the first pending approval
    approval = pending[0]
    approval_id = approval["id"]
    user_id = message.from_user.id if message.from_user else None

    try:
        result = await client.approve_approval(approval_id, {"approved_by": user_id})
        await message.answer(
            f"✅ Approval <code>{html_escape(str(result.get('action', 'unknown')))}</code> — <b>approved</b>.",
            parse_mode="HTML",
        )
    except Exception as exc:
        await message.answer(format_error_message("Approve failed", str(exc)))
        return

    # Show updated task card
    try:
        task = await client.get_task(task_id)
    except Exception:
        pass

    # Check remaining pending approvals
    has_pending = False
    next_approval_id = None
    try:
        approvals = await client.list_approvals_by_task(task_id)
        for a in approvals:
            if a.get("status") == "pending":
                has_pending = True
                next_approval_id = a.get("id")
                break
    except Exception:
        pass

    text = format_task_card(task)
    keyboard = build_task_keyboard(
        task_id=task_id,
        task_status=task.get("status", ""),
        has_pending_approval=has_pending,
        approval_id=next_approval_id,
        has_plan=bool(task.get("plan_text")),
    )

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
