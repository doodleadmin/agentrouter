"""TG-03: /plan <task_id|external_id> — display task plan with inline actions."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.keyboards import build_plan_keyboard
from app.services import get_api_client
from app.services.formatters import format_error_message, format_plan_excerpt

router = Router(name="plan")


@router.message(Command("plan"))
async def plan_handler(message: Message) -> None:
    client = get_api_client()
    args = (message.text or "").strip().split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ Usage: /plan <code>task_id</code> or <code>external_id</code>")
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
    plan_data = await client.get_task_plan(task_id)
    plan_text = plan_data.get("plan_text")
    status = plan_data.get("status", "unknown")

    excerpt = format_plan_excerpt(plan_text)
    header = f"📋 <b>Plan — {task.get('external_id', task_id[:8])}</b>\nStatus: <code>{status}</code>\n\n"

    keyboard = build_plan_keyboard(task.get("external_id") or task_id)

    await message.answer(header + excerpt, reply_markup=keyboard, parse_mode="HTML")
