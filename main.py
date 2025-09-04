import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from keyboard import main_menu
from logic import router as logic_router

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")


async def start_bot():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    @dp.message(lambda message: message.text == "/start")
    async def cmd_start(message: Message):
        await message.answer(
            "👋 Привет! Я помогу тебе отслеживать траты и сэкономленные деньги.\n\nВыбери действие:",
            reply_markup=main_menu,
        )

    dp.include_router(logic_router)

    print("🤖 Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(start_bot())
