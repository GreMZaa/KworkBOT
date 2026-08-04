import asyncio
import logging
from exchanges.base import Order
import notifier
import llm

logging.basicConfig(level=logging.INFO)


async def main():
    print("Генерация живого ИИ-анализа с рыночной ценой и отправка в Telegram...")

    # Пример заказа заказчика с низкой ценой
    order = Order(
        title="нужна настройка телеграмм через сервис Green-Api с ACM CRM",
        description="нужна настройка телеграмм через сервис Green-Api с ACM CRM. Через 2-3 недели необходимо будет WA так же через этот сервис. Плюс настройка телефонии через зебру.",
        price="2 000 руб.",
        deadline="До 3 дней",
        client="termopochta",
        source="Kwork",
        url="https://kwork.ru/projects/3229792/view"
    )

    print(f"1. Вызов Cohere AI для оценки реальной рыночной цены и аналитики...")
    deep_data = await llm.analyze_order_deep(order.title, order.description, client_price=order.price)
    
    print("\nРезультат ИИ-Анализа:")
    for k, v in deep_data.items():
        print(f"  • {k}: {v}")

    print("\n2. Отправка карточки с рыночной ценой в Telegram...")
    await notifier.send_order_notification(order, relevance=90, deep_analysis=deep_data)
    print("✓ Сообщение с рыночной ценой успешно отправлено!")


if __name__ == "__main__":
    asyncio.run(main())
