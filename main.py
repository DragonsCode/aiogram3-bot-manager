import asyncio
import logging
from typing import List
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command, CommandObject
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.utils.markdown import html_decoration as fmt
from aiogram.utils.token import TokenValidationError

from polls import PollingManager

from dotenv import load_dotenv

load_dotenv()

logger = logging.basicConfig(level=logging.INFO)

TOKENS = [ os.getenv('TOKEN')
]
ADMIN_ID = 235519518


async def set_commands(bot: Bot):
    commands = [
        BotCommand(
            command="add",
            description="создать бота, использовать так: '/add ТОКЕН'",
        ),
        BotCommand(
            command="stop",
            description="остановть бота, использовать так: '/stop АЙДИ'",
        ),
    ]

    await bot.set_my_commands(commands=commands, scope=BotCommandScopeDefault())


async def on_bot_startup(bot: Bot):
    await set_commands(bot)
    await bot.send_message(chat_id=ADMIN_ID, text="Бот запущен")


async def on_bot_shutdown(bot: Bot):
    await bot.send_message(chat_id=ADMIN_ID, text="Бот отключен")


async def on_startup(bots: List[Bot]):
    for bot in bots:
        await on_bot_startup(bot)


async def on_shutdown(bots: List[Bot]):
    for bot in bots:
        await on_bot_shutdown(bot)


async def add_bot(
    message: types.Message,
    command: CommandObject,
    dp_for_new_bot: Dispatcher,
    polling_manager: PollingManager,
):
    if command.args:
        try:
            bot = Bot(command.args)

            if bot.id in polling_manager.polling_tasks:
                await message.answer("Такой бот уже запущен")
                return

            
            polling_manager.start_bot_polling(
                dp=dp_for_new_bot,
                bot=bot,
                on_bot_startup=on_bot_startup(bot),
                on_bot_shutdown=on_bot_shutdown(bot),
                polling_manager=polling_manager,
                dp_for_new_bot=dp_for_new_bot,
            )
            bot_user = await bot.get_me()
            await message.answer(f"Бот успешно запущен: @{bot_user.username}")
        except (TokenValidationError, TelegramUnauthorizedError) as err:
            await message.answer(fmt.quote(f"{type(err).__name__}: {str(err)}"))
    else:
        await message.answer("Вы не указали токен бота")


async def stop_bot(
    message: types.Message, command: CommandObject, polling_manager: PollingManager
):
    if command.args:
        try:
            polling_manager.stop_bot_polling(int(command.args))
            await message.answer("Бот остановлен")
        except (ValueError, KeyError) as err:
            await message.answer(fmt.quote(f"{type(err).__name__}: {str(err)}"))
    else:
        await message.answer("Вы не указали айди бота")


async def echo(message: types.Message):
    await message.answer(message.text)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    bots = [Bot(token) for token in TOKENS]
    dp = Dispatcher()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.message.register(add_bot, Command(commands="add"))
    dp.message.register(stop_bot, Command(commands="stop"))
    dp.message.register(echo)

    polling_manager = PollingManager()

    for bot in bots:
        await bot.get_updates(offset=-1)
    await dp.start_polling(*bots, dp_for_new_bot=dp, polling_manager=polling_manager)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Пока")