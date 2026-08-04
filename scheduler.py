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
    
    # 0. Инициализация БД для поддержки таблиц настроек
    await db.init_db()

    # Получаем динамические пороги релевантности и навыки если переопределены
    db_threshold = await db.get_setting("RELEVANCE_THRESHOLD", str(config.RELEVANCE_THRESHOLD))
    try:
        active_threshold = int(db_threshold)
    except ValueError:
        active_threshold = config.RELEVANCE_THRESHOLD

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

                # 3. Проверяем на мошенничество / скам
                is_scam, scam_reason = llm.check_is_scam(order.title, order.description)

                # 4. Сохраняем заказ в базу данных
                await db.save_order(order, relevance)

                # 5. Если релевантность соответствует порогу — выполняем глубокий ИИ-анализ и отправляем в Telegram
                if relevance >= active_threshold:
                    logger.info(f"Заказ '{order.title}' соответствует порогу ({relevance}% >= {active_threshold}%). Глубокий анализ...")
                    deep_analysis = await llm.analyze_order_deep(order.title, order.description, client_price=order.price)
                    
                    await notifier.send_order_notification(
                        order,
                        relevance,
                        is_scam=is_scam,
                        scam_reason=scam_reason,
                        deep_analysis=deep_analysis
                    )

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
