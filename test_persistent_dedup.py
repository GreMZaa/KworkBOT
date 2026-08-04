import asyncio
import logging
from exchanges.base import Order
import db

logging.basicConfig(level=logging.INFO)


async def main():
    print("--- ТЕСТ ДЕДУПЛИКАЦИИ: ПРОВЕРКА ЗАЩИТЫ ОТ ПОВТОРНЫХ УВЕДОМЛЕНИЙ ---")
    await db.init_db()

    test_url = "https://kwork.ru/projects/3229792/view"

    # 1. Проверяем, существует ли заказ
    exists_before = await db.order_exists(test_url)
    print(f"1. Существует ли заказ '{test_url}' до сохранения? -> {exists_before}")

    # 2. Сохраняем заказ в кэш и БД
    dummy_order = Order(
        title="Тестовый заказ для проверки дедупликации",
        description="Описание заказа",
        price="1000 руб",
        deadline="1 день",
        client="Тестер",
        source="Kwork",
        url=test_url
    )
    saved = await db.save_order(dummy_order, relevance=90)
    print(f"2. Сохранение заказа: {saved}")

    # 3. Проверяем сразу же повторно
    exists_after = await db.order_exists(test_url)
    print(f"3. Существует ли заказ '{test_url}' после сохранения? -> {exists_after}")

    assert exists_after is True, "ОШИБКА: Заказ должен быть заблокирован как дубликат!"
    print("✓ ТЕСТ УСПЕШНО ПРОЙДЕН! Повторные заказы гарантированно блокируются!")


if __name__ == "__main__":
    asyncio.run(main())
