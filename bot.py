import asyncio
import logging

import betterlogging as bl
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram.types import (BotCommand, BotCommandScopeDefault,
                           MenuButtonCommands)

from database import scheduler
from tgbot.config import Config, load_config
from tgbot.handlers import user_router
from tgbot.middlewares.config import ConfigMiddleware


async def on_startup(bot: Bot, admin_ids: list[int]) -> None:
    """Регистрирует команды бота и меню."""
    commands = [
        BotCommand(command="start", description="Перезапуск бота"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())


def register_global_middlewares(
    dp: Dispatcher, config: Config, session_pool=None
) -> None:
    """Регистрирует глобальные middleware."""
    middlewares = [ConfigMiddleware(config)]
    for middleware in middlewares:
        dp.message.outer_middleware(middleware)
        dp.callback_query.outer_middleware(middleware)


def setup_logging() -> None:
    """Настройка цветного логирования."""
    bl.basic_colorized_config(level=logging.INFO)
    logging.getLogger(__name__).info("🚀 Starting bot...")


def get_storage(config: Config) -> BaseStorage:
    """Возвращает хранилище (Redis или Memory)."""
    if config.tg_bot.use_redis:
        return RedisStorage.from_url(
            config.redis.dsn(),
            key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
        )
    return MemoryStorage()


async def main() -> None:
    """Основная точка входа."""
    setup_logging()
    config = load_config(".env")
    storage = get_storage(config)

    bot = Bot(
        token=config.tg_bot.token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher(storage=storage)
    dp.include_router(user_router)
    register_global_middlewares(dp, config)
    asyncio.create_task(scheduler())

    await on_startup(bot, config.tg_bot.admin_ids)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("🛑 Бот остановлен корректно")
