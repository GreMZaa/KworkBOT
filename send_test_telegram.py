import asyncio
import logging
from exchanges.base import Order
import config
import notifier
import llm

logging.basicConfig(level=logging.INFO)


async def main():
    print("Отправка тестовых уведомлений в ваш Telegram...")

    # 1. Тестовый заказ Kwork
    order1 = Order(
        title="Разработать Telegram бота на Python (Aiogram 3) с приемом платежей",
        description="Ищем опытного разработчика для создания Telegram бота под ключ. Необходима реализация интерактивного меню, базы данных SQLite, админ-панели и приема платежей. Код должен быть на Python (aiogram 3).",
        price="15 000 руб.",
        deadline="3 дня",
        client="Алексей (Kwork)",
        source="Kwork",
        url="https://kwork.ru/projects"
    )

    print("1. Генерация ИИ-отклика для заказа Kwork...")
    cover1 = await llm.generate_cover_letter(order1.title, order1.description)
    print("Отправка первого заказа в Telegram...")
    await notifier.send_order_notification(order1, relevance=95, cover_letter=cover1)

    await asyncio.sleep(1)

    # 2. Тестовый заказ FL.ru
    order2 = Order(
        title="Парсинг товаров интернет-магазина (10 000 карточек) в Excel",
        description="Требуется оперативно спарсить цены, артикулы, характеристики и ссылки на изображения с сайта интернет-магазина. Выгрузка в формат XLSX. Скрипт на Python (BeautifulSoup / Playwright).",
        price="9 500 руб.",
        deadline="2 дня",
        client="Екатерина (FL.ru)",
        source="FL.ru",
        url="https://www.fl.ru/projects/"
    )

    print("2. Генерация ИИ-отклика для заказа FL.ru...")
    cover2 = await llm.generate_cover_letter(order2.title, order2.description)
    print("Отправка второго заказа в Telegram...")
    await notifier.send_order_notification(order2, relevance=88, cover_letter=cover2)

    print("✓ Все тестовые сообщения успешно отправлены в Telegram!")


if __name__ == "__main__":
    asyncio.run(main())
