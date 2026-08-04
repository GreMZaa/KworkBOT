import logging
import aiohttp
from bs4 import BeautifulSoup
from exchanges.base import Exchange, Order
import config

logger = logging.getLogger(__name__)


class YandexUslugiExchange(Exchange):
    """Парсер реальных заказов с биржи Яндекс.Услуги."""
    name: str = "Яндекс.Услуги"
    base_url: str = "https://uslugi.yandex.ru"
    orders_url: str = "https://uslugi.yandex.ru/freelance"

    async def fetch_orders(self, session: aiohttp.ClientSession) -> list[Order]:
        """
        Получает список свежих заказов с Яндекс.Услуги.

        :param session: Активная сессия aiohttp.ClientSession
        :return: Список объектов Order
        """
        orders: list[Order] = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        if config.YANDEX_COOKIES:
            headers["Cookie"] = config.YANDEX_COOKIES

        try:
            async with session.get(self.orders_url, headers=headers, timeout=15) as response:
                if response.status != 200:
                    logger.error(f"Яндекс.Услуги вернул статус {response.status}")
                    return orders

                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                cards = soup.select("div[class*='OrderCard'], div[class*='TaskCard'], article, div[class*='Card']")
                logger.info(f"Найдено элементов на Яндекс.Услуги: {len(cards)}")

                for card in cards:
                    try:
                        title_elem = card.select_one("h3 a, a[href*='/profile/'], a[href*='/orders/'], a[href*='/task/']")
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        raw_href = title_elem.get("href", "").strip()
                        if not raw_href:
                            continue

                        if raw_href.startswith("http://") or raw_href.startswith("https://"):
                            url = raw_href
                        else:
                            if not raw_href.startswith("/"):
                                raw_href = "/" + raw_href
                            url = f"{self.base_url}{raw_href}"

                        desc_elem = card.select_one("p, div[class*='description'], div[class*='text']")
                        description = desc_elem.get_text(strip=True) if desc_elem else title

                        price_elem = card.select_one("span[class*='price'], div[class*='price']")
                        price = price_elem.get_text(strip=True) if price_elem else "Договорная"

                        client_elem = card.select_one("span[class*='name'], div[class*='user']")
                        client = client_elem.get_text(strip=True) if client_elem else "Заказчик Яндекс"

                        order = Order(
                            title=title,
                            description=description,
                            price=price,
                            deadline="По договоренности",
                            client=client,
                            source=self.name,
                            url=url
                        )
                        orders.append(order)
                    except Exception as card_err:
                        logger.warning(f"Ошибка при разборе карточки Яндекс.Услуги: {card_err}")

        except Exception as e:
            logger.error(f"Ошибка при получении заказов Яндекс.Услуги: {e}")

        return orders
