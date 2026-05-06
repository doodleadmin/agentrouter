"""Handler for /topic_status command."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services import get_api_client

router = Router(name="topic_status")


@router.message(Command("topic_status"))
async def topic_status_handler(message: Message) -> None:
    thread_id = message.message_thread_id
    if thread_id is None:
        await message.answer("⚠️ /topic_status доступна только внутри forum topic.")
        return

    client = get_api_client()
    current = await client.find_topic_binding(message.chat.id, thread_id)
    if current is None:
        await message.answer(
            (
                "ℹ️ Привязка не найдена.\n"
                f"chat_id={message.chat.id}\n"
                f"message_thread_id={thread_id}\n"
                "status=unbound"
            ),
        )
        return

    await message.answer(
        (
            "📌 Topic status\n"
            f"chat_id={current.get('chat_id')}\n"
            f"message_thread_id={current.get('message_thread_id')}\n"
            f"project_id={current.get('project_id')}\n"
            f"agent_id={current.get('agent_id')}\n"
            f"status={'active' if current.get('is_active') else 'inactive'}"
        ),
    )
