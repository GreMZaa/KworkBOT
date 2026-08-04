import asyncio
import logging
import sys
from aiogram import Dispatcher
import config
import db
import scheduler
from notifier import bot

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
    if bot:
        dp = Dispatcher()

        @dp.startup()
        def on_startup():
            logger.info("Telegram-бот успешно подключен и готов к работе.")

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
