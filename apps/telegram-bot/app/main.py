"""Entrypoint for Telegram Bot Gateway (polling mode for dev)."""

import asyncio
import logging

from app.bot import create_bot, create_dispatcher
from app.config import settings
from app.services import close_api_client


async def run_polling() -> None:
    """Run bot in polling mode (dev)."""

    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is empty. Configure token in environment.")

    bot = create_bot()
    dp = create_dispatcher()
    try:
        await dp.start_polling(bot, allowed_updates=settings.POLLING_ALLOWED_UPDATES)
    finally:
        await close_api_client()
        await bot.session.close()


def main() -> None:
    """CLI entrypoint."""

    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_polling())


if __name__ == "__main__":
    main()
