"""Bot/dispatcher factory for Telegram gateway."""

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.handlers import (
    bind_topic_router,
    commands_router,
    messages_router,
    start_router,
    topic_status_router,
    unbind_topic_router,
)


def create_bot() -> Bot:
    """Create configured aiogram Bot instance."""

    return Bot(token=settings.TELEGRAM_BOT_TOKEN, parse_mode=ParseMode.HTML)


def create_dispatcher() -> Dispatcher:
    """Create dispatcher and register TG-01/TG-02 routers."""

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start_router)
    dp.include_router(commands_router)
    dp.include_router(bind_topic_router)
    dp.include_router(unbind_topic_router)
    dp.include_router(topic_status_router)
    dp.include_router(messages_router)
    return dp
