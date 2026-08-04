import aiosqlite
import logging
import json
import os
import hashlib
import aiohttp
from exchanges.base import Order
import config

logger = logging.getLogger(__name__)

# Путь к локальному файлу кэша просмотренных заказов
SEEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seen_orders.json")

# Облачный REST KV эндпоинт для гарантированной стойкости на Vercel
KV_API_URL = "https://api.kvstore.io/v1/items"
KV_KEY = "kworkbot_seen_hashes"

_seen_cache: set[str] = set()


def _hash_url(url: str) -> str:
    """Хеширует URL заказа для компактного хранения."""
    return hashlib.md5(url.strip().encode("utf-8")).hexdigest()


def _load_local_cache():
    """Загружает кэш хешей из локального файла seen_orders.json."""
    global _seen_cache
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                _seen_cache.update(data)
                logger.info(f"Загружено из seen_orders.json: {len(data)} хешей заказов.")
        except Exception as e:
            logger.warning(f"Ошибка чтения seen_orders.json: {e}")


def _save_local_cache():
    """Сохраняет кэш хешей в локальный файл seen_orders.json."""
    try:
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(list(_seen_cache), f, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Ошибка записи seen_orders.json: {e}")


async def init_db():
    """Инициализация базы данных SQLite и загрузка стойкого кэша дедупликации."""
    _load_local_cache()

    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                price TEXT,
                deadline TEXT,
                client TEXT,
                source TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                relevance INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        await db.commit()

        # Импортируем существующие URL из базы SQLite в кэш
        async with db.execute("SELECT url FROM orders") as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                _seen_cache.add(_hash_url(row[0]))
        _save_local_cache()
        logger.info(f"База данных и кэш дедупликации инициализированы. Запомнено заказов: {len(_seen_cache)}")


async def order_exists(url: str) -> bool:
    """
    Двухуровневая проверка дедупликации:
    1. Проверка в кэше оперативной памяти (_seen_cache)
    2. Проверка в SQLite базе данных
    """
    url_h = _hash_url(url)
    if url_h in _seen_cache:
        logger.debug(f"Заказ {url} найден в _seen_cache. Пропуск дубликата.")
        return True

    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute("SELECT 1 FROM orders WHERE url = ?", (url,)) as cursor:
            row = await cursor.fetchone()
            if row is not None:
                _seen_cache.add(url_h)
                _save_local_cache()
                return True

    return False


async def save_order(order: Order, relevance: int = 0) -> bool:
    """
    Сохраняет новый заказ в базу данных и регистрирует в стойком кэше.
    """
    url_h = _hash_url(order.url)
    _seen_cache.add(url_h)
    _save_local_cache()

    async with aiosqlite.connect(config.DB_PATH) as db:
        try:
            await db.execute("""
                INSERT INTO orders (title, description, price, deadline, client, source, url, relevance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order.title,
                order.description,
                order.price,
                order.deadline,
                order.client,
                order.source,
                order.url,
                relevance
            ))
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            logger.debug(f"Заказ с URL {order.url} уже существует в БД.")
            return False
        except Exception as e:
            logger.error(f"Ошибка сохранения заказа в БД: {e}")
            return False


async def get_setting(key: str, default: str = "") -> str:
    """Получает значение настройки из БД, если нет — возвращает default."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
            return default


async def set_setting(key: str, value: str):
    """Сохраняет или обновляет значение настройки в БД."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        await db.commit()


async def get_stats_summary() -> dict:
    """Возвращает агрегированную статистику по заказам из БД."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM orders") as cursor:
            total_orders = (await cursor.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM orders WHERE created_at >= datetime('now', '-1 day')") as cursor:
            today_orders = (await cursor.fetchone())[0]

        async with db.execute("SELECT source, COUNT(*) FROM orders GROUP BY source") as cursor:
            sources_breakdown = dict(await cursor.fetchall())

        async with db.execute("SELECT AVG(relevance) FROM orders WHERE relevance > 0") as cursor:
            avg_rel_row = await cursor.fetchone()
            avg_relevance = round(avg_rel_row[0], 1) if avg_rel_row and avg_rel_row[0] else 0.0

        return {
            "total": total_orders,
            "today": today_orders,
            "sources": sources_breakdown,
            "avg_relevance": avg_relevance
        }
