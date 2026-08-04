from http.server import BaseHTTPRequestHandler
import asyncio
import aiohttp
import sys
import os

# Добавляем корневую директорию проекта в sys.path для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
import scheduler


class handler(BaseHTTPRequestHandler):
    """
    Vercel Serverless Function Handler.
    Вызывается автоматически сервисом Vercel Cron по расписанию.
    """

    def do_GET(self):
        async def run_cron():
            await db.init_db()
            async with aiohttp.ClientSession() as session:
                await scheduler.poll_exchanges_once(session)

        try:
            asyncio.run(run_cron())
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok", "message": "Poll completed successfully"}')
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_msg = f'{{"status": "error", "message": "{str(e)}"}}'
            self.wfile.write(error_msg.encode('utf-8'))
        return
