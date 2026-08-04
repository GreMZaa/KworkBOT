import asyncio
import aiohttp
import re
import json
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
        url = "https://kwork.ru/projects"
        async with session.get(url, headers=headers) as resp:
            text = await resp.text()
            soup = BeautifulSoup(text, "html.parser")

            # Выводим заголовок страницы
            print("Title:", soup.title.string if soup.title else "No title")

            # Поиск всех JSON в скриптах
            for script in soup.find_all("script"):
                if script.string:
                    if "wants" in script.string.lower() or "projects" in script.string.lower() or "want" in script.string.lower():
                        matches = re.findall(r'window\.(\w+)\s*=\s*(\{.*\}|\[.*\]);', script.string)
                        for var_name, json_str in matches:
                            if "want" in var_name.lower() or "project" in var_name.lower() or "data" in var_name.lower():
                                print(f"Var found: window.{var_name} (length {len(json_str)})")

            # Проверяем все div и ссылки на странице
            print("\nПроверка всех ссылок на проекты:")
            project_links = soup.find_all("a", href=re.compile(r'/projects/\d+'))
            print(f"Найдено прямо ссылок /projects/ID: {len(project_links)}")
            for a in project_links[:10]:
                print(f"  Link: {a.get_text(strip=True)} -> {a.get('href')}")

            # Ищем отфильтрованные карточки
            all_cards = soup.find_all(class_=re.compile(r'want|card|project', re.I))
            print(f"\nВсего связанных классов: {len(all_cards)}")
            for c in all_cards[:10]:
                print(f"  Class: {c.get('class')} | Text: {c.get_text(strip=True)[:60]}")

if __name__ == "__main__":
    asyncio.run(main())
