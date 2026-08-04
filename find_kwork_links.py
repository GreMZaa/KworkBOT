import asyncio
import aiohttp
from bs4 import BeautifulSoup
import config

async def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    if config.KWORK_COOKIES:
        headers["Cookie"] = config.KWORK_COOKIES

    async with aiohttp.ClientSession() as session:
        async with session.get("https://kwork.ru/projects", headers=headers) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            
            # Находим все ссылки с текстом
            links = soup.find_all("a")
            print("Total <a> tags:", len(links))
            for a in links:
                href = a.get("href", "")
                text = a.get_text(strip=True)
                if ("project" in href or "target" in href or "want" in href) and len(text) > 5:
                    print("LINK:", text, "->", href)

if __name__ == "__main__":
    asyncio.run(main())
