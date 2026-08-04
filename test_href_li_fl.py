import asyncio
import logging
from exchanges.base import Order
import notifier
import llm

logging.basicConfig(level=logging.INFO)


async def main():
    print("Отправка заказа с FL.ru через анонимайзер href.li для обхода 403...")

    order = Order(
        title="Разработка ИИ-менеджера для автосалона",
        description="Необходимо разработать голосового ИИ-рекрутера/менеджера для автоматизации первичного подбора персонала и обзвона клиентов на Python.",
        price="По договоренности",
        deadline="Стандартный",
        client="Заказчик FL",
        source="FL.ru",
        url="https://www.fl.ru/projects/5516515/razrabotka-ii-menedjera-.html"
    )

    deep_data = await llm.analyze_order_deep(order.title, order.description, client_price=order.price)
    await notifier.send_order_notification(order, relevance=85, deep_analysis=deep_data)
    print("✓ Заказ FL.ru с обходом 403 успешно отправлен в Telegram!")


if __name__ == "__main__":
    asyncio.run(main())
