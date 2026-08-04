import aiosqlite
import logging
from exchanges.base import Order
import config

logger = logging.getLogger(__name__)


async def init_db():
    """Инициализация базы данных SQLite и создание таблиц orders и settings."""
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
        logger.info(f"База данных успешно инициализирована: {config.DB_PATH}")


async def order_exists(url: str) -> bool:
    """
    Проверяет, существует ли заказ с данным url в базе данных.
    """
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute("SELECT 1 FROM orders WHERE url = ?", (url,)) as cursor:
            row = await cursor.fetchone()
            return row is not None


async def save_order(order: Order, relevance: int = 0) -> bool:
    """
    Сохраняет новый заказ в базу данных.
    """
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
