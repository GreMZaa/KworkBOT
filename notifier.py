import logging
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from exchanges.base import Order
import config

logger = logging.getLogger(__name__)

# Инициализация экземпляра бота (если задан токен)
bot: Bot | None = None
if config.TELEGRAM_BOT_TOKEN:
    bot = Bot(
        token=config.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )


def format_order_message(order: Order, relevance: int) -> str:
    """
    Форматирует информацию о заказе в HTML-сообщение для Telegram.

    :param order: Объект Order
    :param relevance: Процент релевантности (0–100)
    :return: Отформатированная HTML-строка
    """
    message = (
        f"🎯 <b>Новый релевантный заказ! ({relevance}%)</b>\n\n"
        f"📌 <b>Источник:</b> {order.source}\n"
        f"📝 <b>Заголовок:</b> <a href='{order.url}'>{order.title}</a>\n"
        f"💰 <b>Бюджет:</b> {order.price or 'Не указан'}\n"
        f"⏱ <b>Срок:</b> {order.deadline or 'Не указан'}\n"
        f"👤 <b>Заказчик:</b> {order.client or 'Не указан'}\n\n"
        f"📄 <b>Описание:</b>\n<i>{order.description[:500]}{'...' if len(order.description) > 500 else ''}</i>\n\n"
        f"🔗 <a href='{order.url}'>Открыть заказ на бирже</a>"
    )
    return message


async def send_order_notification(order: Order, relevance: int) -> bool:
    """
    Отправляет уведомление о заказе в Telegram-чат.

    :param order: Объект Order
    :param relevance: Процент релевантности (0–100)
    :return: True при успешной отправке, иначе False
    """
    global bot
    if not bot:
        if config.TELEGRAM_BOT_TOKEN:
            bot = Bot(
                token=config.TELEGRAM_BOT_TOKEN,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )
        else:
            logger.warning("TELEGRAM_BOT_TOKEN не задан. Уведомление не отправлено.")
            return False

    if not config.TELEGRAM_CHAT_ID:
        logger.warning("TELEGRAM_CHAT_ID не задан. Уведомление не отправлено.")
        return False

    text = format_order_message(order, relevance)

    try:
        await bot.send_message(
            chat_id=config.TELEGRAM_CHAT_ID,
            text=text,
            disable_web_page_preview=False
        )
        logger.info(f"Уведомление о заказе '{order.title}' успешно отправлено в Telegram.")
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")
        return False
