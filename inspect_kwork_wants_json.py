import asyncio
import aiohttp
import json
from bs4 import BeautifulSoup
import config


async def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
    }
    if config.KWORK_COOKIES:
        headers["Cookie"] = config.KWORK_COOKIES

    async with aiohttp.ClientSession() as session:
        # 1. Запрос к JSON API Kwork проектов (wants)
        endpoints = [
            "https://kwork.ru/projects",
            "https://kwork.ru/raw-wants",
            "https://kwork.ru/api/project/list",
        ]
        
        for url in endpoints:
            print(f"\nЗапрос {url} ...")
            try:
                async with session.get(url, headers=headers) as resp:
                    print(f"Status: {resp.status}, Content-Type: {resp.headers.get('Content-Type')}")
                    text = await resp.text()
                    if "json" in resp.headers.get("Content-Type", ""):
                        data = json.loads(text)
                        print("JSON keys:", data.keys() if isinstance(data, dict) else len(data))
                    else:
                        soup = BeautifulSoup(text, "html.parser")
                        # Поиск встройенного состояния (state / initial-data)
                        scripts = soup.find_all("script")
                        for s in scripts:
                            if s.string and ("window.wants" in s.string or "state" in s.string or "projects" in s.string):
                                print("Найдено совпадение в script:", s.string[:300])
            except Exception as e:
                print(f"Ошибка {url}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
