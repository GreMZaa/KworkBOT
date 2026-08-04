import html
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


def get_clean_redirect_url(url: str) -> str:
    """
    Очищает URL от Referer-заголовка Telegram через анонимайзер href.li, 
    чтобы обходить блокировки 403 Cloudflare на FL.ru и Kwork.
    """
    clean_url = url.strip()
    if clean_url.startswith("https://href.li/?"):
        return clean_url
    return f"https://href.li/?{clean_url}"


def format_order_message(order: Order, relevance: int, deep_analysis: dict = None, is_scam: bool = False, scam_reason: str = "") -> str:
    """
    Форматирует расширенную информацию о заказе с защитой от 403 Cloudflare.
    """
    safe_title = html.escape(order.title)
    raw_url = order.url.strip()
    bypass_url = get_clean_redirect_url(raw_url)
    
    safe_source = html.escape(order.source)
    safe_price = html.escape(order.price or "Не указан")
    safe_deadline = html.escape(order.deadline or "Не указан")
    safe_client = html.escape(order.client or "Не указан")
    
    desc_raw = order.description[:400] + ("..." if len(order.description) > 400 else "")
    safe_description = html.escape(desc_raw)

    scam_header = ""
    if is_scam:
        scam_header = f"⚠️ <b>ВНИМАНИЕ: ВОЗМОЖЕН СКАМ / МОШЕННИЧЕСТВО!</b>\n<i>({html.escape(scam_reason)})</i>\n\n"

    # Данные глубокого ИИ-анализа
    market_price = html.escape(deep_analysis.get("market_price", "Не определена") if deep_analysis else "3 000 — 5 000 руб.")
    difficulty = html.escape(deep_analysis.get("difficulty", "Средняя") if deep_analysis else "Средняя")
    estimated_time = html.escape(deep_analysis.get("estimated_time", "2-4 часа") if deep_analysis else "2-4 часа")
    tech_stack = html.escape(deep_analysis.get("tech_stack", "Python") if deep_analysis else "Python")
    ai_tip = html.escape(deep_analysis.get("ai_tip", "") if deep_analysis else "")
    hashtags = html.escape(deep_analysis.get("hashtags", "#python #freelance") if deep_analysis else "#python #freelance")
    cover_letter = deep_analysis.get("cover_letter", "") if deep_analysis else ""

    message = (
        f"{scam_header}"
        f"🎯 <b>Новый релевантный заказ! ({relevance}%)</b>\n\n"
        f"📌 <b>Источник:</b> {safe_source}\n"
        f"📝 <b>Заголовок:</b> <a href='{bypass_url}'>{safe_title}</a>\n"
        f"💰 <b>Бюджет клиента:</b> {safe_price}\n"
        f"💵 <b>Реальная рыночная цена:</b> <b>{market_price}</b> 💎\n"
        f"⏱ <b>Срок заказчика:</b> {safe_deadline}\n"
        f"👤 <b>Заказчик:</b> {safe_client}\n\n"
        f"🧠 <b>ИИ-Анализ задачи:</b>\n"
        f"• <b>Сложность:</b> {difficulty}\n"
        f"• <b>Ориентировочное время:</b> {estimated_time}\n"
        f"• <b>Рекомендуемый стек:</b> <code>{tech_stack}</code>\n\n"
    )

    if ai_tip:
        message += f"💡 <b>Совет к отклику:</b>\n<i>{ai_tip}</i>\n\n"

    message += (
        f"📄 <b>Описание:</b>\n<i>{safe_description}</i>\n"
    )

    if cover_letter:
        safe_cover_letter = html.escape(cover_letter)
        message += (
            f"\n🤖 <b>Готовый ИИ-отклик (нажмите чтобы скопировать):</b>\n"
            f"<code>{safe_cover_letter}</code>\n"
        )

    message += (
        f"\n🔗 <b>Прямая ссылка (без 403):</b>\n{bypass_url}\n\n"
        f"📋 <b>Ссылка для копирования:</b>\n<code>{html.escape(raw_url)}</code>\n\n"
        f"{hashtags}"
    )

    return message


def get_order_inline_keyboard(order: Order) -> InlineKeyboardMarkup:
    """
    Создает Inline-кнопку с обходом реферера Telegram (href.li) для гарантированного открытия без 403.
    """
    bypass_url = get_clean_redirect_url(order.url)
    button_text = f"🚀 Откликнуться на {order.source}"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=button_text, url=bypass_url)]
        ]
    )
    return keyboard


async def send_order_notification(order: Order, relevance: int, cover_letter: str = "", is_scam: bool = False, scam_reason: str = "", deep_analysis: dict = None) -> bool:
    """
    Отправляет уведомление о заказе в Telegram.
    """
    bot = get_bot()
    if not bot:
        logger.warning("TELEGRAM_BOT_TOKEN не задан или Bot не инициализирован.")
        return False

    if not config.TELEGRAM_CHAT_ID:
        logger.warning("TELEGRAM_CHAT_ID не задан. Уведомление не отправлено.")
        return False

    text = format_order_message(order, relevance, deep_analysis=deep_analysis, is_scam=is_scam, scam_reason=scam_reason)
    reply_markup = get_order_inline_keyboard(order)

    try:
        await bot.send_message(
            chat_id=config.TELEGRAM_CHAT_ID,
            text=text,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        logger.info(f"Уведомление о заказе '{order.title}' успешно отправлено в Telegram.")
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")
        return False
