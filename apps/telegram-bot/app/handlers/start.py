"""Start/help handlers."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="start")


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    await message.answer(
        (
            "👋 Agent Mission Control Bot\n\n"
            "Команды:\n"
            "/help — справка\n"
            "/projects — активные проекты\n"
            "/agents — активные агенты\n"
            "/tasks — последние задачи"
        ),
    )


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        (
            "ℹ️ TG-01 режим:\n"
            "- /projects, /agents, /tasks читают данные из backend API\n"
            "- обычный текст создаёт Task, если topic привязан\n"
            "- запуск runtime/агентов пока отключён"
        ),
    )
