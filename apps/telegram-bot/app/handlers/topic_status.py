"""Handler for /topic_status command."""

from html import escape as html_escape

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services import get_api_client

router = Router(name="topic_status")


@router.message(Command("topic_status"))
async def topic_status_handler(message: Message) -> None:
    is_private = message.chat.type == "private"
    thread_id = message.message_thread_id if not is_private else (message.message_thread_id or 0)

    client = get_api_client()
    current = await client.find_topic_binding(message.chat.id, thread_id)
    if current is None:
        label = "чат" if is_private else "topic"
        await message.answer(
            (
                f"ℹ️ Привязка для {label} не найдена.\n"
                f"chat_id={message.chat.id}\n"
                f"message_thread_id={thread_id}\n"
                "status=unbound"
            ),
        )
        return

    label = "Чат" if is_private else "Topic"
    await message.answer(
        (
            f"📌 {label} status\n"
            f"chat_id={current.get('chat_id')}\n"
            f"message_thread_id={current.get('message_thread_id')}\n"
            f"project_id={html_escape(str(current.get('project_id', 'N/A')))}\n"
            f"agent_id={html_escape(str(current.get('agent_id', 'N/A')))}\n"
            f"status={'active' if current.get('is_active') else 'inactive'}"
        ),
    )
