import asyncio
import aiohttp
from bs4 import BeautifulSoup


async def main():
    async with aiohttp.ClientSession() as session:
        # Kwork RSS
        print("Тестирование Kwork RSS...")
        async with session.get("https://kwork.ru/rss", headers={"User-Agent": "Mozilla/5.0"}) as resp:
            print("Kwork RSS статус:", resp.status)
            if resp.status == 200:
                xml = await resp.text()
                soup = BeautifulSoup(xml, "xml")
                items = soup.find_all("item")
                print(f"Kwork RSS вернул {len(items)} заказов")
                for it in items[:3]:
                    print("  - Kwork:", it.title.text if it.title else "", "|", it.link.text if it.link else "")

        # FL.ru RSS
        print("\nТестирование FL.ru RSS...")
        async with session.get("https://www.fl.ru/rss/all.xml", headers={"User-Agent": "Mozilla/5.0"}) as resp:
            print("FL.ru RSS статус:", resp.status)
            if resp.status == 200:
                xml = await resp.text()
                soup = BeautifulSoup(xml, "xml")
                items = soup.find_all("item")
                print(f"FL.ru RSS вернул {len(items)} заказов")
                for it in items[:3]:
                    print("  - FL.ru:", it.title.text if it.title else "", "|", it.link.text if it.link else "")

        # Habr Freelance RSS
        print("\nТестирование Habr Freelance RSS...")
        async with session.get("https://freelance.habr.com/tasks.rss", headers={"User-Agent": "Mozilla/5.0"}) as resp:
            print("Habr RSS статус:", resp.status)
            if resp.status == 200:
                xml = await resp.text()
                soup = BeautifulSoup(xml, "xml")
                items = soup.find_all("item")
                print(f"Habr RSS вернул {len(items)} заказов")
                for it in items[:3]:
                    print("  - Habr:", it.title.text if it.title else "", "|", it.link.text if it.link else "")

if __name__ == "__main__":
    asyncio.run(main())
