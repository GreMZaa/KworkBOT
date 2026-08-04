import aiosqlite
import logging
from exchanges.base import Order
import config

logger = logging.getLogger(__name__)


async def init_db():
    """Инициализация базы данных SQLite и создание таблицы orders при отсутствии."""
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
        await db.commit()
        logger.info(f"База данных успешно инициализирована: {config.DB_PATH}")


async def order_exists(url: str) -> bool:
    """
    Проверяет, существует ли заказ с данным url в базе данных.

    :param url: Уникальная ссылка на заказ
    :return: True, если заказ уже есть в БД, иначе False
    """
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute("SELECT 1 FROM orders WHERE url = ?", (url,)) as cursor:
            row = await cursor.fetchone()
            return row is not None


async def save_order(order: Order, relevance: int = 0) -> bool:
    """
    Сохраняет новый заказ в базу данных.

    :param order: Объект Order
    :param relevance: Оценка релевантности в процентах (0-100)
    :return: True, если заказ успешно сохранен, False при дубликате или ошибке
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
            # Заказ с таким url уже существует
            return False
        except Exception as e:
            logger.error(f"Ошибка при сохранении заказа {order.url}: {e}")
            return False
