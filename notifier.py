import logging
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from exchanges.base import Order
import config

logger = logging.getLogger(__name__)

_bot_instance: Bot | None = None


def get_bot() -> Bot | None:
    """Ленивая инициализация экземпляра aiogram.Bot при вызове."""
    global _bot_instance
    if _bot_instance is None and config.TELEGRAM_BOT_TOKEN:
        try:
            _bot_instance = Bot(
                token=config.TELEGRAM_BOT_TOKEN,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )
        except Exception as e:
            logger.error(f"Ошибка инициализации Bot: {e}")
            _bot_instance = None
    return _bot_instance


def format_order_message(order: Order, relevance: int, cover_letter: str = "") -> str:
    """
    Форматирует информацию о заказе и готовую запись отклика для Telegram.

    :param order: Объект Order
    :param relevance: Процент релевантности (0–100)
    :param cover_letter: Сгенерированный текст отклика от ИИ
    :return: Отформатированная HTML-строка
    """
    message = (
        f"🎯 <b>Новый релевантный заказ! ({relevance}%)</b>\n\n"
        f"📌 <b>Источник:</b> {order.source}\n"
        f"📝 <b>Заголовок:</b> <a href='{order.url}'>{order.title}</a>\n"
        f"💰 <b>Бюджет:</b> {order.price or 'Не указан'}\n"
        f"⏱ <b>Срок:</b> {order.deadline or 'Не указан'}\n"
        f"👤 <b>Заказчик:</b> {order.client or 'Не указан'}\n\n"
        f"📄 <b>Описание:</b>\n<i>{order.description[:400]}{'...' if len(order.description) > 400 else ''}</i>\n"
    )

    if cover_letter:
        message += (
            f"\n🤖 <b>Готовый ИИ-отклик (нажмите чтобы скопировать):</b>\n"
            f"<code>{cover_letter}</code>\n"
        )

    return message


def get_order_inline_keyboard(order: Order) -> InlineKeyboardMarkup:
    """
    Создает Inline-кнопку для быстрого перехода на страницу заказа.
    """
    button_text = f"🚀 Откликнуться на {order.source}"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=button_text, url=order.url)]
        ]
    )
    return keyboard


async def send_order_notification(order: Order, relevance: int, cover_letter: str = "") -> bool:
    """
    Отправляет уведомление о заказе с кнопкой быстрого отклика в Telegram.

    :param order: Объект Order
    :param relevance: Процент релевантности (0–100)
    :param cover_letter: Текст сопроводительного письма от ИИ
    :return: True при успешной отправке, иначе False
    """
    bot = get_bot()
    if not bot:
        logger.warning("TELEGRAM_BOT_TOKEN не задан или Bot не инициализирован.")
        return False

    if not config.TELEGRAM_CHAT_ID:
        logger.warning("TELEGRAM_CHAT_ID не задан. Уведомление не отправлено.")
        return False

    text = format_order_message(order, relevance, cover_letter)
    reply_markup = get_order_inline_keyboard(order)

    try:
        await bot.send_message(
            chat_id=config.TELEGRAM_CHAT_ID,
            text=text,
            reply_markup=reply_markup,
            disable_web_page_preview=False
        )
        logger.info(f"Уведомление о заказе '{order.title}' успешно отправлено в Telegram.")
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")
        return False
