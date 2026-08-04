import asyncio
import logging
from exchanges.base import Order
import config
import db
import notifier
import llm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_system")


async def run_tests():
    logger.info("--- СТАРТ ТЕСТИРОВАНИЯ СИСТЕМЫ ---")

    # 1. Проверка инициализации БД
    logger.info("1. Проверка инициализации базы данных SQLite...")
    await db.init_db()
    assert config.DB_PATH.exists(), "Файл orders.db не был создан!"
    logger.info("✓ База данных создана успешно.")

    # 2. Создание тестового заказа
    test_order = Order(
        title="Разработка Telegram бота на Python (aiogram)",
        description="Требуется разработать Telegram бота для мониторинга заказов с биржи Kwork. Стек: Python, aiogram 3, SQLite.",
        price="15 000 руб.",
        deadline="3 дня",
        client="Иван Петров",
        source="Kwork",
        url="https://kwork.ru/projects/test-12345"
    )

    # 3. Проверка записи и уникальности заказа в БД
    logger.info("2. Проверка функций работы с БД (save_order и order_exists)...")
    exists_before = await db.order_exists(test_order.url)
    logger.info(f"Существует ли тестовый заказ до сохранения: {exists_before}")

    saved = await db.save_order(test_order, relevance=95)
    logger.info(f"Результат первого сохранения заказа: {saved}")

    exists_after = await db.order_exists(test_order.url)
    assert exists_after is True, "Заказ не найден в БД после сохранения!"

    duplicate_save = await db.save_order(test_order, relevance=95)
    assert duplicate_save is False, "Дубликат заказа был ошибочно сохранен!"
    logger.info("✓ Защита от дубликатов в БД работает корректно.")

    # 4. Проверка форматирования уведомления
    logger.info("3. Проверка форматирования HTML-сообщения...")
    msg = notifier.format_order_message(test_order, relevance=95)
    assert "Telegram бота" in msg and "Kwork" in msg, "Форматирование сообщения некорректно!"
    logger.info("✓ Форматирование HTML-сообщения работает корректно.")

    # 5. Тестирование Cohere API (обработка фоллбэка без токена)
    logger.info("4. Проверка Cohere API (обработка фоллбэка при отсутствии токена)...")
    relevance = await llm.evaluate_relevance(test_order.title, test_order.description)
    logger.info(f"Полученный результат оценки релевантности: {relevance}%")

    logger.info("--- ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ! ---")


if __name__ == "__main__":
    asyncio.run(run_tests())
