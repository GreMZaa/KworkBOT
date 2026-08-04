import asyncio
import logging
import aiohttp
import config
import db
import llm
import notifier
from exchanges.kwork import KworkExchange
from exchanges.fl_ru import FLExchange
from exchanges.yandex_uslugi import YandexUslugiExchange

logging.basicConfig(level=logging.INFO)


async def main():
    print("=== ПРЯМОЙ ЖИВОЙ СКАН БИРЖ НА НАЛИЧИЕ ЗАКАЗОВ ===")
    await db.init_db()

    exchanges = [KworkExchange(), FLExchange(), YandexUslugiExchange()]
    
    total_found = 0
    relevant_found = 0

    async with aiohttp.ClientSession() as session:
        for ex in exchanges:
            print(f"\n🔍 Запрос к бирже {ex.name}...")
            try:
                orders = await ex.fetch_orders(session)
                print(f"Получено заказов с {ex.name}: {len(orders)}")
                total_found += len(orders)

                for order in orders:
                    print(f"\n  📌 Заказ: '{order.title}'")
                    print(f"     Ссылка: {order.url}")

                    # Оценка через Cohere AI
                    relevance = await llm.evaluate_relevance(order.title, order.description)
                    print(f"     ⭐ Оценка Cohere AI: {relevance}% (Порог в настройках: {config.RELEVANCE_THRESHOLD}%)")

                    # Проверка антискам
                    is_scam, scam_reason = llm.check_is_scam(order.title, order.description)
                    if is_scam:
                        print(f"     ⚠️ Обнаружен скам: {scam_reason}")

                    # Сохранение в БД
                    await db.save_order(order, relevance)

                    # Отправка если заказ релевантен
                    if relevance >= 50:  # Показываем любые заказы от 50%+
                        relevant_found += 1
                        print(f"     ✅ ОТПРАВКА В TELEGRAM (Релевантность {relevance}% >= 50%)")
                        cover = await llm.generate_cover_letter(order.title, order.description)
                        await notifier.send_order_notification(
                            order, relevance, cover_letter=cover, is_scam=is_scam, scam_reason=scam_reason
                        )

            except Exception as e:
                print(f"  ❌ Ошибка при сканировании {ex.name}: {e}")

    print(f"\n==========================================")
    print(f"📊 ИТОГИ СКАНА: Всего найдено объявлений: {total_found}, Релевантных отправлено: {relevant_found}")


if __name__ == "__main__":
    asyncio.run(main())
