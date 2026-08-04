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
    logger.info("--- СТАРТ ТЕСТИРОВАНИЯ СИСТЕМЫ С ИИ-ОТКЛИКАМИ И INLINE-КНОПКАМИ ---")

    # 1. Проверка инициализации БД
    await db.init_db()

    # 2. Создание тестового заказа
    test_order = Order(
        title="Разработка Telegram бота на Python (aiogram)",
        description="Требуется разработать Telegram бота для мониторинга заказов с биржи Kwork. Стек: Python, aiogram 3, SQLite.",
        price="15 000 руб.",
        deadline="3 дня",
        client="Иван Петров",
        source="Kwork",
        url="https://kwork.ru/projects/test-99999"
    )

    # 3. Оценка релевантности через Cohere API
    logger.info("1. Оценка релевантности заказа через Cohere AI...")
    relevance = await llm.evaluate_relevance(test_order.title, test_order.description)
    logger.info(f"Оценка релевантности: {relevance}%")

    # 4. Генерация ИИ сопроводительного письма (Cover Letter)
    logger.info("2. Генерация ИИ сопроводительного письма...")
    cover_letter = await llm.generate_cover_letter(test_order.title, test_order.description)
    logger.info(f"Сгенерированный отклик:\n{cover_letter}")
    assert len(cover_letter) > 10, "Отклик от ИИ не был сгенерирован!"

    # 5. Проверка форматирования сообщения и Inline-кнопок
    logger.info("3. Проверка форматирования сообщения и Inline-кнопки...")
    msg = notifier.format_order_message(test_order, relevance, cover_letter)
    kb = notifier.get_order_inline_keyboard(test_order)

    assert "Готовый ИИ-отклик" in msg, "Блок отклика отсутствует в сообщении!"
    assert kb.inline_keyboard[0][0].url == test_order.url, "URL кнопки ведет на некорректный адрес!"
    logger.info("✓ Сообщение и Inline-кнопки успешно сформированы.")

    logger.info("--- ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ! ---")


if __name__ == "__main__":
    asyncio.run(run_tests())
