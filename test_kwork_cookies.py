import asyncio
import aiohttp
from bs4 import BeautifulSoup
import config

async def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    if config.KWORK_COOKIES:
        headers["Cookie"] = config.KWORK_COOKIES

    async with aiohttp.ClientSession() as session:
        print("Проверка kwork.ru/projects с куками...")
        async with session.get("https://kwork.ru/projects", headers=headers) as resp:
            print("Status:", resp.status)
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            
            # Различные селекторы
            wants = soup.select(".wants-card, .want-card, div[class*='want'], .projects-list div")
            print("Найдено карточек проектов:", len(wants))
            
            # Ссылки на проекты
            links = soup.select("a[href*='/projects/']")
            print("Найдено ссылок /projects/:", len(links))
            for l in links[:5]:
                print("  ->", l.get_text(strip=True), "|", l.get("href"))

if __name__ == "__main__":
    asyncio.run(main())
