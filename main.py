import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from keyboard import main_menu
from logic import router as logic_router
from sql import connect_database, renew_active_subscriptions

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def renew_subscriptions():
    logger.info("Running monthly subscription renewal.")

    try:
        await renew_active_subscriptions()
        logger.info("Monthly renewal completed")

    except Exception as e:
        logger.error(f"Error during renewal: {e}")


async def start_bot():
    await connect_database()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    @dp.message(lambda message: message.text == "/start")
    async def command_start(message: Message):
        await message.answer(
            "👋 Hello! I will help you track your expenses and saved money.\n\nPlease choose an action:",
            reply_markup=main_menu,
        )

    dp.include_router(logic_router)

    scheduler.add_job(
        renew_subscriptions,
        trigger=CronTrigger(day=1, hour=1, minute=1),
        id="subscriptions_renewal",
        replace_existing=True,
    )
    scheduler.start()

    logger.info("Bot started.")
    logger.info("Scheduler initialized.")

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(start_bot())
