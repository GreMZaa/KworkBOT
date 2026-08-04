import asyncio
import aiohttp
from bs4 import BeautifulSoup
import config


async def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    if config.KWORK_COOKIES:
        headers["Cookie"] = config.KWORK_COOKIES

    async with aiohttp.ClientSession() as session:
        # Проверяем биржу заказов Kwork (проекты покупателей)
        for url in ["https://kwork.ru/projects?c=11", "https://kwork.com/projects?c=11", "https://kwork.ru/projects"]:
            print(f"\nЗапрос к бирже проектов: {url} ...")
            async with session.get(url, headers=headers) as resp:
                print("Status:", resp.status)
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")
                    
                    # Ищем карточки покупательских заказов
                    cards = soup.select(".wants-card, .want-card, div[class*='wants-card'], .project-card")
                    print(f"Найдено ПОКУПАТЕЛЬСКИХ заказов: {len(cards)}")
                    
                    for i, card in enumerate(cards[:5]):
                        title_elem = card.select_one(".wants-card__header-title a, a[href*='/projects/'], a[href*='/target']")
                        price_elem = card.select_one(".wants-card__header-price, .price, span[class*='price']")
                        
                        title = title_elem.get_text(strip=True) if title_elem else "Без названия"
                        href = title_elem.get("href", "") if title_elem else ""
                        price = price_elem.get_text(strip=True) if price_elem else "Не указан"
                        
                        print(f"  [{i+1}] ЗАКАЗ ЗАКАЗЧИКА: '{title}' | {price} | href: {href}")

if __name__ == "__main__":
    asyncio.run(main())
