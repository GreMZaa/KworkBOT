import asyncio
import aiohttp
import json
import config


async def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }
    if config.KWORK_COOKIES:
        headers["Cookie"] = config.KWORK_COOKIES

    url = "https://kwork.ru/projects"
    data = {"c": "11"}  # Категория 11 = Разработка и IT

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=data) as resp:
            if resp.status == 200:
                res = await resp.json()
                items = res.get("data", {}).get("pagination", {}).get("data", [])
                print(f"=== ПОКУПАТЕЛЬСКИЕ ЗАКАЗЫ С KWORK (Найдено {len(items)} шт.) ===")
                for i, item in enumerate(items[:10]):
                    proj_id = item.get("id")
                    title = item.get("title", "Без названия")
                    desc = item.get("description", "Без описания")
                    price = item.get("priceLimit", item.get("price", "Договорная"))
                    kworks_cnt = item.get("kworksCount", 0)
                    client_name = item.get("username", item.get("user", {}).get("username", "Заказчик"))
                    
                    proj_url = f"https://kwork.ru/projects/{proj_id}/view"
                    print(f"\n[{i+1}] ЗАКАЗ ЗАКАЗЧИКА ID {proj_id}:")
                    print(f"    Заголовок: {title}")
                    print(f"    Бюджет: {price} руб.")
                    print(f"    Заказчик: {client_name}")
                    print(f"    Откликов: {kworks_cnt}")
                    print(f"    Ссылка: {proj_url}")
                    print(f"    Описание: {desc[:150]}...")

if __name__ == "__main__":
    asyncio.run(main())
