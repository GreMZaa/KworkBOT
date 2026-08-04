import asyncio
import logging
import sys
from aiogram import Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
import config
import db
import scheduler
from notifier import get_bot

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("main")


async def main():
    logger.info("Запуск Telegram-бота мониторинга фриланс-бирж...")

    # 1. Инициализация базы данных SQLite
    await db.init_db()

    # 2. Запуск фоновой задачи планировщика
    scheduler_task = asyncio.create_task(scheduler.start_scheduler())

    # 3. Запуск Telegram бота (если задан TELEGRAM_BOT_TOKEN)
    bot = get_bot()
    if bot:
        dp = Dispatcher()

        @dp.startup()
        def on_startup():
            logger.info("Telegram-бот успешно подключен и готов к работе.")

        @dp.message(CommandStart())
        async def command_start_handler(message: Message):
            skills_list = config.MY_SKILLS
            await message.answer(
                f"👋 <b>Привет, {message.from_user.first_name}!</b>\n\n"
                f"🤖 Я бот-монитор фриланс-бирж (Kwork, Яндекс.Услуги и др.).\n\n"
                f"📊 Я сканирую заказы, оцениваю их соответствие навыкам через Cohere AI "
                f"и моментально присылаю вам заказы с релевантностью от {config.RELEVANCE_THRESHOLD}%+.\n\n"
                f"🎯 <b>Ваши навыки:</b> {skills_list}\n"
                f"🆔 <b>Ваш Chat ID:</b> <code>{message.chat.id}</code>"
            )

        @dp.message(Command("help"))
        async def command_help_handler(message: Message):
            await message.answer(
                "📋 <b>Справка бота:</b>\n\n"
                "/start - Приветствие и информация о настройках\n"
                "/help - Показать эту справку"
            )

        try:
            logger.info("Старт polling Telegram-бота...")
            await dp.start_polling(bot)
        except Exception as e:
            logger.error(f"Ошибка при работе Telegram-бота: {e}")
        finally:
            scheduler_task.cancel()
            await bot.session.close()
    else:
        logger.warning("TELEGRAM_BOT_TOKEN не задан. Бот запущен в режиме автономного планировщика.")
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Работа бота остановлена пользователем.")
