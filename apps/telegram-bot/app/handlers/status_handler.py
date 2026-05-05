"""TG-03: /status <task_id|external_id> — display task card with inline actions."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.keyboards import build_task_keyboard
from app.services import get_api_client
from app.services.formatters import format_error_message, format_task_card

router = Router(name="status")


def _thread_id(message: Message) -> int | None:
    return message.message_thread_id


@router.message(Command("status"))
async def status_handler(message: Message) -> None:
    client = get_api_client()
    args = (message.text or "").strip().split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "⚠️ Usage: /status <task_id|external_id>",
            message_thread_id=_thread_id(message),
        )
        return

    task_ref = args[1].strip()

    # Try as UUID first, then as external_id
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
            message_thread_id=_thread_id(message),
        )
        return

    task_id = task["id"]
    task_status = task.get("status", "")

    # Check for pending approvals
    has_pending = False
    approval_id = None
    try:
        approvals = await client.list_approvals_by_task(task_id)
        for a in approvals:
            if a.get("status") == "pending":
                has_pending = True
                approval_id = a.get("id")
                break
    except Exception:
        pass

    has_plan = bool(task.get("plan_text"))

    text = format_task_card(task)
    keyboard = build_task_keyboard(
        task_id=task_id,
        task_status=task_status,
        has_pending_approval=has_pending,
        approval_id=approval_id,
        has_plan=has_plan,
    )

    await message.answer(text, reply_markup=keyboard, message_thread_id=_thread_id(message), parse_mode="HTML")
