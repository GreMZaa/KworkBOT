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
        async with session.get("https://kwork.ru/projects", headers=headers) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            
            wants = soup.select(".wants-card, .want-card")
            print("Wants found:", len(wants))
            for i, w in enumerate(wants[:3]):
                print(f"\n--- CARD {i+1} ---")
                print("HTML:", w.prettify()[:600])

if __name__ == "__main__":
    asyncio.run(main())
