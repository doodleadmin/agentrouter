"""Handler for /unbind_topic command (soft deactivate)."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services import get_api_client

router = Router(name="unbind_topic")


@router.message(Command("unbind_topic"))
async def unbind_topic_handler(message: Message) -> None:
    is_private = message.chat.type == "private"
    thread_id = message.message_thread_id if not is_private else (message.message_thread_id or 0)

    client = get_api_client()
    current = await client.find_topic_binding(message.chat.id, thread_id)
    if current is None:
        label = "чат" if is_private else "Topic"
        await message.answer(f"ℹ️ {label} ещё не привязан.")
        return

    await client.deactivate_topic_binding(current["id"])
    label = "Чат" if is_private else "Topic"
    await message.answer(f"✅ {label} отвязан (soft deactivate).")
