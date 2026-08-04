import asyncio
import logging
import aiohttp
import config
import db
import llm
import notifier

logger = logging.getLogger(__name__)


async def poll_exchanges_once(session: aiohttp.ClientSession):
    """
    Выполняет один цикл опроса всех зарегистрированных фриланс-бирж.
    """
    logger.info("Начало цикла опроса бирж...")
    for exchange in config.EXCHANGES:
        try:
            logger.info(f"Опрос биржи {exchange.name}...")
            orders = await exchange.fetch_orders(session)
            logger.info(f"Получено заказов с {exchange.name}: {len(orders)}")

            for order in orders:
                # 1. Проверяем, был ли заказ сохранен ранее
                if await db.order_exists(order.url):
                    continue

                # 2. Оцениваем релевантность заказа через Cohere API
                relevance = await llm.evaluate_relevance(order.title, order.description)

                # 3. Сохраняем заказ в базу данных
                await db.save_order(order, relevance)

                # 4. Если релевантность соответствует порогу — генерируем ИИ-отклик и отправляем в Telegram
                if relevance >= config.RELEVANCE_THRESHOLD:
                    logger.info(f"Заказ '{order.title}' подходить под порог ({relevance}% >= {config.RELEVANCE_THRESHOLD}%). Генерация ИИ-отклика...")
                    cover_letter = await llm.generate_cover_letter(order.title, order.description)
                    await notifier.send_order_notification(order, relevance, cover_letter)

        except Exception as e:
            logger.error(f"Ошибка при обработке биржи {exchange.name}: {e}", exc_info=True)


async def start_scheduler():
    """
    Фоновый цикл планировщика, выполняющий опрос бирж каждые POLL_INTERVAL_SECONDS секунд.
    """
    logger.info(f"Планировщик запущен. Интервал опроса: {config.POLL_INTERVAL_SECONDS} секунд.")
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                await poll_exchanges_once(session)
        except Exception as e:
            logger.error(f"Ошибка в цикле планировщика: {e}", exc_info=True)

        await asyncio.sleep(config.POLL_INTERVAL_SECONDS)
