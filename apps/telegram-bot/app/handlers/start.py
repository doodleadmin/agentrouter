"""Start/help handlers."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from app.config import settings

router = Router(name="start")


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    text = (
        "👋 Agent Mission Control Bot\n\n"
        "Команды:\n"
        "/help — справка\n"
        "/projects — активные проекты\n"
        "/agents — активные агенты\n"
        "/tasks — последние задачи"
    )

    is_private = bool(message.chat and str(message.chat.type) == "private")
    if is_private and settings.TELEGRAM_WEBAPP_URL:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Открыть AI Office",
                        web_app=WebAppInfo(url=settings.TELEGRAM_WEBAPP_URL),
                    ),
                ],
            ],
        )
        await message.answer(text, reply_markup=keyboard)
        return

    await message.answer(text)


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
