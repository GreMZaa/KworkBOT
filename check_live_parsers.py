import asyncio
import logging
import aiohttp
import config
from exchanges.kwork import KworkExchange
from exchanges.yandex_uslugi import YandexUslugiExchange
from exchanges.fl_ru import FLExchange

logging.basicConfig(level=logging.INFO)


async def main():
    print("--- ПРОВЕРКА РЕАЛЬНОГО ПАРСИНГА БИРЖ ---")
    async with aiohttp.ClientSession() as session:
        # 1. Kwork
        kw = KworkExchange()
        print("\n1. Проверка Kwork...")
        kw_orders = await kw.fetch_orders(session)
        print(f"Kwork вернул {len(kw_orders)} заказов")
        for o in kw_orders[:3]:
            print(f"  - [{o.source}] {o.title} | {o.price} | {o.url}")

        # 2. FL.ru
        fl = FLExchange()
        print("\n2. Проверка FL.ru...")
        fl_orders = await fl.fetch_orders(session)
        print(f"FL.ru вернул {len(fl_orders)} заказов")
        for o in fl_orders[:3]:
            print(f"  - [{o.source}] {o.title} | {o.price} | {o.url}")

        # 3. Yandex Uslugi
        yu = YandexUslugiExchange()
        print("\n3. Проверка Яндекс.Услуги...")
        yu_orders = await yu.fetch_orders(session)
        print(f"Яндекс.Услуги вернул {len(yu_orders)} заказов")
        for o in yu_orders[:3]:
            print(f"  - [{o.source}] {o.title} | {o.price} | {o.url}")


if __name__ == "__main__":
    asyncio.run(main())
