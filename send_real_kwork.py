import asyncio
import aiohttp
from bs4 import BeautifulSoup
from exchanges.base import Order
import config
import notifier
import llm


async def main():
    print("Получение РЕАЛЬНОГО живого проекта с Kwork...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    
    real_link = ""
    real_title = ""
    real_desc = ""

    async with aiohttp.ClientSession() as session:
        async with session.get("https://kwork.ru/rss", headers=headers) as resp:
            if resp.status == 200:
                xml = await resp.text()
                soup = BeautifulSoup(xml, "xml")
                items = soup.find_all("item")
                if items:
                    it = items[0]
                    real_title = it.title.text.strip() if it.title else "Реальный проект Kwork"
                    real_link = it.link.text.strip() if it.link else "https://kwork.ru"
                    real_desc = it.description.text.strip() if it.description else real_title

    if real_link:
        print(f"Найден живой проект: {real_title} -> {real_link}")
        order = Order(
            title=real_title,
            description=real_desc,
            price="По договоренности",
            deadline="1 день",
            client="Заказчик Kwork",
            source="Kwork",
            url=real_link
        )
        
        cover = await llm.generate_cover_letter(order.title, order.description)
        await notifier.send_order_notification(order, relevance=92, cover_letter=cover)
        print("✓ Уведомление с РЕАЛЬНОЙ живой ссылкой отправлено в ваш Telegram!")
    else:
        print("Не удалось извлечь живую ссылку.")


if __name__ == "__main__":
    asyncio.run(main())
