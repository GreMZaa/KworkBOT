import asyncio
import logging
import config
import db
import scheduler
from notifier import get_bot
from aiogram import Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message):
    await db.init_db()
    current_skills = await db.get_setting("MY_SKILLS", config.MY_SKILLS)
    current_threshold = await db.get_setting("RELEVANCE_THRESHOLD", str(config.RELEVANCE_THRESHOLD))
    await message.answer(
        f"👋 <b>Привет, {message.from_user.first_name}!</b>\n\n"
        f"🤖 Я бот-монитор фриланс-бирж (Kwork, Яндекс.Услуги, FL.ru).\n\n"
        f"📊 Я опрашиваю биржи, оцениваю заказы через Cohere AI "
        f"и присылаю вам подходящие заказы с совпадением от {current_threshold}%+.\n\n"
        f"🎯 <b>Ваши навыки:</b> {current_skills}\n"
        f"🆔 <b>Ваш Chat ID:</b> <code>{message.chat.id}</code>\n\n"
        f"💡 Напишите /help для просмотра доступных команд управления."
    )


@dp.message(Command("help"))
async def command_help_handler(message: Message):
    await message.answer(
        "📋 <b>Команды управления ботом:</b>\n\n"
        "📊 /stats — Статистика найденных заказов\n"
        "🎯 /skills — Просмотр и изменение навыков\n"
        "⚙️ /threshold — Настройка порога фильтрации\n"
        "❓ /help — Справка"
    )


@dp.message(Command("stats"))
async def command_stats_handler(message: Message):
    await db.init_db()
    stats = await db.get_stats_summary()
    sources_text = "\n".join([f"• <b>{k}:</b> {v} шт." for k, v in stats["sources"].items()]) or "Пока нет данных"
    await message.answer(
        f"📊 <b>Статистика мониторинга заказов:</b>\n\n"
        f"📁 <b>Всего найдено заказов:</b> {stats['total']} шт.\n"
        f"📅 <b>Найдено за последние 24ч:</b> {stats['today']} шт.\n"
        f"⭐ <b>Средняя релевантность:</b> {stats['avg_relevance']}%\n\n"
        f"🌐 <b>По биржам:</b>\n{sources_text}"
    )


@dp.message(Command("skills"))
async def command_skills_handler(message: Message):
    await db.init_db()
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        new_skills = args[1].strip()
        await db.set_setting("MY_SKILLS", new_skills)
        config.MY_SKILLS = new_skills
        await message.answer(f"✅ <b>Навыки успешно обновлены:</b>\n<code>{new_skills}</code>")
    else:
        current_skills = await db.get_setting("MY_SKILLS", config.MY_SKILLS)
        await message.answer(
            f"🎯 <b>Текущие навыки для ИИ-оценки:</b>\n<code>{current_skills}</code>\n\n"
            f"💡 <i>Чтобы изменить навыки, отправьте:</i>\n"
            f"<code>/skills Python, aiogram, парсинг, React</code>"
        )


@dp.message(Command("threshold"))
async def command_threshold_handler(message: Message):
    await db.init_db()
    args = message.text.split(maxsplit=1)
    if len(args) > 1 and args[1].strip().isdigit():
        val = int(args[1].strip())
        if 0 <= val <= 100:
            await db.set_setting("RELEVANCE_THRESHOLD", str(val))
            config.RELEVANCE_THRESHOLD = val
            await message.answer(f"✅ <b>Минимальный порог отбора заказов установлен на {val}%</b>")
        else:
            await message.answer("⚠️ Введите число от 0 до 100. Пример: <code>/threshold 80</code>")
    else:
        current_val = await db.get_setting("RELEVANCE_THRESHOLD", str(config.RELEVANCE_THRESHOLD))
        await message.answer(
            f"⚙️ <b>Текущий порог фильтрации:</b> {current_val}%\n\n"
            f"💡 <i>Чтобы изменить порог, отправьте:</i>\n"
            f"<code>/threshold 80</code>"
        )


async def main():
    logger.info("Инициализация базы данных...")
    await db.init_db()

    bot = get_bot()
    if not bot:
        logger.error("Ошибка: TELEGRAM_BOT_TOKEN не задан в .env")
        return

    logger.info("Запуск фонового планировщика...")
    asyncio.create_task(scheduler.start_scheduler())

    logger.info("Запуск Telegram-бота в режиме Long Polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
