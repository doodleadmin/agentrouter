"""Command handlers backed by Orchestrator API."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services import get_api_client

router = Router(name="commands")


@router.message(Command("projects"))
async def projects_handler(message: Message) -> None:
    client = get_api_client()
    items = await client.list_projects()
    if not items:
        text = "📦 Проекты не найдены."
    else:
        lines = ["📦 Активные проекты:"]
        for p in items[:20]:
            lines.append(f"• {p.get('slug')} — {p.get('name')}")
        text = "\n".join(lines)
    await message.answer(text)


@router.message(Command("agents"))
async def agents_handler(message: Message) -> None:
    client = get_api_client()
    items = await client.list_agents()
    if not items:
        text = "🤖 Агенты не найдены."
    else:
        lines = ["🤖 Активные агенты:"]
        for a in items[:20]:
            lines.append(f"• {a.get('slug')} ({a.get('role')})")
        text = "\n".join(lines)
    await message.answer(text)


@router.message(Command("tasks"))
async def tasks_handler(message: Message) -> None:
    client = get_api_client()
    items = await client.list_tasks(limit=20)
    if not items:
        text = "🧩 Задачи не найдены."
    else:
        lines = ["🧩 Последние задачи:"]
        for t in items[:20]:
            lines.append(f"• {t.get('external_id')} | {t.get('status')} | {t.get('title')}")
        text = "\n".join(lines)
    await message.answer(text)
