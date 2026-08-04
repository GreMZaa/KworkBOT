import logging
import aiohttp
from bs4 import BeautifulSoup
from exchanges.base import Exchange, Order
import config

logger = logging.getLogger(__name__)


class KworkExchange(Exchange):
    """Парсер реальных заказов с биржи Kwork."""
    name: str = "Kwork"
    base_url: str = "https://kwork.ru"
    projects_url: str = "https://kwork.ru/projects"

    async def fetch_orders(self, session: aiohttp.ClientSession) -> list[Order]:
        """
        Получает список свежих заказов с биржи Kwork (биржа проектов).

        :param session: Активная сессия aiohttp.ClientSession
        :return: Список объектов Order
        """
        orders: list[Order] = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        if config.KWORK_COOKIES:
            headers["Cookie"] = config.KWORK_COOKIES

        try:
            async with session.get(self.projects_url, headers=headers, timeout=15) as response:
                if response.status != 200:
                    logger.error(f"Kwork повернул статус {response.status}")
                    return orders

                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                # Находим карточки проектов Kwork
                cards = soup.select(".wants-card, .want-card, div[class*='wants-card']")
                logger.info(f"Найдено карточек проектов на Kwork: {len(cards)}")

                for card in cards:
                    try:
                        # Заголовок и ссылка
                        title_elem = card.select_one(".wants-card__header-title a, a[href*='/projects/']")
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        raw_href = title_elem.get("href", "").strip()
                        if not raw_href:
                            continue

                        # Исправление формирования корректного URL со слэшем
                        if raw_href.startswith("http://") or raw_href.startswith("https://"):
                            url = raw_href
                        else:
                            if not raw_href.startswith("/"):
                                raw_href = "/" + raw_href
                            url = f"{self.base_url}{raw_href}"

                        # Описание
                        desc_elem = card.select_one(".wants-card__description-text, .wants-card__text, div[class*='description']")
                        description = desc_elem.get_text(strip=True) if desc_elem else title

                        # Бюджет / Стоимость
                        price_elem = card.select_one(".wants-card__header-price, .price, span[class*='price']")
                        price = price_elem.get_text(strip=True) if price_elem else "Не указан"

                        # Заказчик / Автор
                        client_elem = card.select_one(".wants-card__user-name, .user-name, a[href*='/user/']")
                        client = client_elem.get_text(strip=True) if client_elem else "Заказчик Kwork"

                        # Срок
                        deadline_elem = card.select_one("span[title*='допустимо'], .want-card__time, span[class*='time']")
                        deadline = deadline_elem.get_text(strip=True) if deadline_elem else "Стандартный"

                        order = Order(
                            title=title,
                            description=description,
                            price=price,
                            deadline=deadline,
                            client=client,
                            source=self.name,
                            url=url
                        )
                        orders.append(order)
                    except Exception as card_err:
                        logger.warning(f"Ошибка при разборе карточки Kwork: {card_err}")

        except Exception as e:
            logger.error(f"Ошибка при получении заказов Kwork: {e}")

        return orders
