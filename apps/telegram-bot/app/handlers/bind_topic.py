"""Handler for /bind_topic command."""

from html import escape as html_escape

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services import get_api_client
from app.services.topic_binding import parse_bind_topic_args

router = Router(name="bind_topic")


@router.message(Command("bind_topic"))
async def bind_topic_handler(message: Message) -> None:
    is_private = message.chat.type == "private"
    # Private chats have no message_thread_id; use 0 as sentinel for DB lookup.
    thread_id = message.message_thread_id if not is_private else (message.message_thread_id or 0)

    parsed = parse_bind_topic_args(message.text or "")
    if parsed is None:
        await message.answer("Формат: /bind_topic project=<code>project_slug</code> agent=<code>agent_slug</code>")
        return

    client = get_api_client()

    project = await client.find_project_by_slug(parsed.project_slug)
    if project is None:
        await message.answer(f"❌ Проект '{html_escape(parsed.project_slug)}' не найден.")
        return

    agent = await client.find_agent_by_slug(parsed.agent_slug)
    if agent is None:
        await message.answer(f"❌ Агент '{html_escape(parsed.agent_slug)}' не найден.")
        return

    chat_id = message.chat.id
    title = f"Project:{parsed.project_slug} Agent:{parsed.agent_slug}"

    current = await client.find_topic_binding(chat_id=chat_id, message_thread_id=thread_id)
    if current is None:
        result = await client.create_topic_binding(
            chat_id=chat_id,
            message_thread_id=thread_id,
            title=title,
            project_id=project["id"],
            agent_id=agent["id"],
        )
        action = "создана"
    else:
        result = await client.update_topic_binding(
            topic_id=current["id"],
            title=title,
            project_id=project["id"],
            agent_id=agent["id"],
            is_active=True,
        )
        action = "обновлена"

    label = "чат" if is_private else "topic"
    await message.answer(
        (
            f"✅ Привязка {label} {action}.\n"
            f"project={html_escape(parsed.project_slug)}\n"
            f"agent={html_escape(parsed.agent_slug)}\n"
            f"status={'active' if result.get('is_active') else 'inactive'}"
        ),
    )
