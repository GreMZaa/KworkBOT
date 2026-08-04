from http.server import BaseHTTPRequestHandler
import json
import asyncio
import aiohttp
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram.types import Update
from aiogram import Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
import config
import db
import scheduler
from notifier import get_bot

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


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        """Обработка GET запросов (Vercel Cron / Пинг сервера)"""
        async def run_cron():
            await db.init_db()
            async with aiohttp.ClientSession() as session:
                await scheduler.poll_exchanges_once(session)

        try:
            asyncio.run(run_cron())
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok", "message": "Cron completed"}')
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_msg = f'{{"status": "error", "message": "{str(e)}"}}'
            self.wfile.write(error_msg.encode('utf-8'))

    def do_POST(self):
        """Обработка POST запросов (Telegram Webhook /start и обновления)"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        async def process_update():
            bot = get_bot()
            if bot and post_data:
                data = json.loads(post_data.decode('utf-8'))
                update = Update.model_validate(data, context={"bot": bot})
                await dp.feed_update(bot, update)

        try:
            asyncio.run(process_update())
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_msg = f'{{"status": "error", "message": "{str(e)}"}}'
            self.wfile.write(error_msg.encode('utf-8'))
