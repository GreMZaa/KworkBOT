import logging
import aiohttp
from bs4 import BeautifulSoup
from exchanges.base import Exchange, Order

logger = logging.getLogger(__name__)


class FLExchange(Exchange):
    """Парсер заказов с фриланс-биржи FL.ru."""
    name: str = "FL.ru"
    base_url: str = "https://www.fl.ru"
    projects_url: str = "https://www.fl.ru/projects/"

    async def fetch_orders(self, session: aiohttp.ClientSession) -> list[Order]:
        """
        Получает список свежих проектов с FL.ru.

        :param session: Активная сессия aiohttp.ClientSession
        :return: Список объектов Order
        """
        orders: list[Order] = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        try:
            async with session.get(self.projects_url, headers=headers, timeout=15) as response:
                if response.status != 200:
                    logger.error(f"FL.ru вернул статус {response.status}")
                    return orders

                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                cards = soup.select(".b-post, div[id*='project-item'], div[class*='b-post']")
                logger.info(f"Найдено проектов на FL.ru: {len(cards)}")

                for card in cards:
                    try:
                        title_elem = card.select_one(".b-post__title a, a[href*='/projects/']")
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        raw_href = title_elem.get("href", "")
                        if not raw_href:
                            continue

                        url = raw_href if raw_href.startswith("http") else f"{self.base_url}{raw_href}"

                        desc_elem = card.select_one(".b-post__txt, div[class*='text']")
                        description = desc_elem.get_text(strip=True) if desc_elem else title

                        price_elem = card.select_one(".b-post__price, div[class*='price']")
                        price = price_elem.get_text(strip=True) if price_elem else "По договоренности"

                        client_elem = card.select_one("a[href*='/users/'], .b-post__user")
                        client = client_elem.get_text(strip=True) if client_elem else "Заказчик FL"

                        order = Order(
                            title=title,
                            description=description,
                            price=price,
                            deadline="Стандартный",
                            client=client,
                            source=self.name,
                            url=url
                        )
                        orders.append(order)
                    except Exception as card_err:
                        logger.warning(f"Ошибка при разборе карточки FL.ru: {card_err}")

        except Exception as e:
            logger.error(f"Ошибка при получении заказов FL.ru: {e}")

        return orders
