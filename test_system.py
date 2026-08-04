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
    logger.info("--- СТАРТ ТЕСТИРОВАНИЯ СИСТЕМЫ (ЭТАП 12: АНТИСКАМ И КОМАНДЫ) ---")

    # 1. Проверка инициализации БД и таблицы settings
    await db.init_db()
    await db.set_setting("MY_SKILLS", "Python, aiogram, парсинг")
    saved_skills = await db.get_setting("MY_SKILLS")
    assert saved_skills == "Python, aiogram, парсинг", "Ошибка работы с таблицей settings в БД!"
    logger.info("✓ Сохранение и чтение динамических настроек из БД работает.")

    # 2. Проверка функции статистики get_stats_summary()
    stats = await db.get_stats_summary()
    assert "total" in stats and "today" in stats, "Ошибка получения статистики!"
    logger.info(f"✓ Статистика из БД успешно сформирована: {stats}")

    # 3. Проверка умного антискам-фильтра
    logger.info("3. Проверка антискам-фильтра...")
    scam_order = Order(
        title="Нужно быстро сделать сайт (страховой взнос 500р)",
        description="Сделайте работу, перед стартом внесите залоговый взнос 500 рублей на карту.",
        price="5 000 руб.",
        deadline="1 день",
        client="Мошенник",
        source="Kwork",
        url="https://kwork.ru/projects/test-scam"
    )

    is_scam, scam_reason = llm.check_is_scam(scam_order.title, scam_order.description)
    assert is_scam is True, "Антискам-фильтр не распознал мошеннический заказ!"
    logger.info(f"✓ Антискам-фильтр успешно распознал мошенника: {scam_reason}")

    # 4. Проверка плашки в notifier
    msg = notifier.format_order_message(scam_order, 90, cover_letter="Тестовый отклик", is_scam=is_scam, scam_reason=scam_reason)
    assert "ВНИМАНИЕ: ВОЗМОЖЕН СКАМ" in msg, "Плашка предупреждения о скаме отсутствует в сообщении!"
    logger.info("✓ Сообщение с красной плашкой предупреждения Антискам сформировано идеально.")

    logger.info("--- ВСЕ ТЕСТЫ ЭТАПА 12 УСПЕШНО ПРОЙДЕНЫ! ---")


if __name__ == "__main__":
    asyncio.run(run_tests())
