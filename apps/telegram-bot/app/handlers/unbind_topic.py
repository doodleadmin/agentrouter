"""Handler for /unbind_topic command (soft deactivate)."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services import get_api_client

router = Router(name="unbind_topic")


def _thread_id(message: Message) -> int | None:
    return message.message_thread_id


@router.message(Command("unbind_topic"))
async def unbind_topic_handler(message: Message) -> None:
    if message.message_thread_id is None:
        await message.answer(
            "⚠️ /unbind_topic работает только внутри forum topic.",
            message_thread_id=_thread_id(message),
        )
        return

    client = get_api_client()
    current = await client.find_topic_binding(message.chat.id, message.message_thread_id)
    if current is None:
        await message.answer(
            "ℹ️ Topic ещё не привязан.",
            message_thread_id=_thread_id(message),
        )
        return

    await client.deactivate_topic_binding(current["id"])
    await message.answer(
        "✅ Topic отвязан (soft deactivate).",
        message_thread_id=_thread_id(message),
    )
