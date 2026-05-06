"""Generic message handler for topic-aware task creation + plan pipeline trigger."""

from __future__ import annotations

from html import escape as html_escape

from aiogram import Router
from aiogram.types import Message

from app.services import get_api_client, resolve_topic_context

router = Router(name="messages")


def _make_title(text: str) -> str:
    title = text.strip().replace("\n", " ")
    return title[:120] if len(title) > 120 else title


@router.message()
async def text_message_handler(message: Message) -> None:
    # TG-04: Prevent worker notification feedback loop.
    # Bot messages (including worker-sent notifications) must not trigger
    # task creation or any API calls.  from_user is always present for
    # non-channel messages in private / group chats.
    if message.from_user and message.from_user.is_bot:
        return

    text = (message.text or "").strip()
    if not text:
        return

    # Commands are handled by dedicated command routers.
    if text.startswith("/"):
        return

    chat_id = message.chat.id
    thread_id = message.message_thread_id
    user_id = message.from_user.id if message.from_user else None
    username = message.from_user.username if message.from_user else None

    topic_ctx = await resolve_topic_context(chat_id=chat_id, message_thread_id=thread_id)
    if not topic_ctx.is_bound:
        await message.answer(
            (
                "⚠️ Этот topic пока не привязан в системе.\n"
                "Используйте /bind_topic project=<code>project_slug</code> agent=<code>agent_slug</code>."
            ),
        )
        return

    payload = {
        "title": _make_title(text),
        "raw_text": text,
        "normalized_text": text,
        "risk_level": "low",
        "intent": "telegram_message",
        "project_id": topic_ctx.project_id,
        "agent_id": topic_ctx.agent_id,
        "telegram_chat_id": chat_id,
        "telegram_thread_id": thread_id,
        "created_by": user_id,
    }

    client = get_api_client()
    task = await client.create_task(payload)

    response_lines = [
        "✅ Task создан.",
        f"ID: {html_escape(str(task.get('external_id', 'N/A')))}",
        f"Topic: {html_escape(topic_ctx.title or 'bound-topic')}",
    ]
    if username:
        response_lines.append(f"User: @{html_escape(username)}")

    # Trigger plan pipeline via backend API → Celery agent_plan queue
    task_id = task.get("id")
    if task_id:
        try:
            await client.trigger_plan(task_id)
            response_lines.append("🚀 Plan pipeline запущен.")
        except Exception:
            response_lines.append("⚠️ Plan pipeline не удалось запустить.")

    await message.answer("\n".join(response_lines))
