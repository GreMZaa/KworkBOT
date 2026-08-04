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
    await message.answer(
        f"👋 <b>Привет, {message.from_user.first_name}!</b>\n\n"
        f"🤖 Я бот-монитор фриланс-бирж (Kwork, Яндекс.Услуги).\n\n"
        f"📊 Я опрашиваю биржи, оцениваю заказы через Cohere AI "
        f"и присылаю вам подходящие заказы с совпадением от {config.RELEVANCE_THRESHOLD}%+.\n\n"
        f"🎯 <b>Ваши навыки:</b> {config.MY_SKILLS}\n"
        f"🆔 <b>Ваш Chat ID:</b> <code>{message.chat.id}</code>"
    )


@dp.message(Command("help"))
async def command_help_handler(message: Message):
    await message.answer(
        "📋 <b>Справка бота:</b>\n\n"
        "/start - Приветствие и ваши настройки\n"
        "/help - Справка"
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
