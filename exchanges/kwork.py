import logging
import aiohttp
from bs4 import BeautifulSoup
from exchanges.base import Exchange, Order
import config

logger = logging.getLogger(__name__)


class KworkExchange(Exchange):
    """Парсер реальных заказов с биржи Kwork (поддержка RSS + HTML kwork.com / kwork.ru)."""
    name: str = "Kwork"
    base_url: str = "https://kwork.com"
    rss_url: str = "https://kwork.com/rss"
    projects_url: str = "https://kwork.com/projects"

    async def fetch_orders(self, session: aiohttp.ClientSession) -> list[Order]:
        orders: list[Order] = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        }

        if config.KWORK_COOKIES:
            headers["Cookie"] = config.KWORK_COOKIES

        # 1. Загрузка через RSS ленту kwork.com / kwork.ru
        for rss_endpoint in ["https://kwork.com/rss", "https://kwork.ru/rss"]:
            try:
                async with session.get(rss_endpoint, headers=headers, timeout=12) as response:
                    if response.status == 200:
                        xml_text = await response.text()
                        soup = BeautifulSoup(xml_text, "xml")
                        items = soup.find_all("item")
                        logger.info(f"Найдено элементов в {rss_endpoint}: {len(items)}")

                        for item in items:
                            try:
                                title = item.title.text.strip() if item.title else "Без названия"
                                link = item.link.text.strip() if item.link else ""
                                desc = item.description.text.strip() if item.description else title
                                price = "Договорная"
                                
                                if " za " in title or " за " in title:
                                    sep = " za " if " za " in title else " за "
                                    parts = title.split(sep)
                                    title = parts[0].strip()
                                    price = parts[1].strip()

                                # Заменяем домен на kwork.com для бесшовного открытия в сессии пользователя
                                if link:
                                    clean_link = link.replace("kwork.ru", "kwork.com")
                                    order = Order(
                                        title=title,
                                        description=desc,
                                        price=price,
                                        deadline="Стандартный",
                                        client="Заказчик Kwork",
                                        source=self.name,
                                        url=clean_link
                                    )
                                    orders.append(order)
                            except Exception as item_err:
                                logger.warning(f"Ошибка парсинга элемента Kwork RSS: {item_err}")
                        if orders:
                            break
            except Exception as e:
                logger.error(f"Ошибка при получении Kwork RSS ({rss_endpoint}): {e}")

        # 2. Дополнительно извлекаем через HTML биржи проектов Kwork
        if not orders:
            for proj_endpoint in ["https://kwork.com/projects", "https://kwork.ru/projects"]:
                try:
                    async with session.get(proj_endpoint, headers=headers, timeout=12) as response:
                        if response.status == 200:
                            html_text = await response.text()
                            soup = BeautifulSoup(html_text, "html.parser")
                            cards = soup.select(".wants-card, .want-card, div[class*='want']")
                            logger.info(f"Найдено карточек проектов на {proj_endpoint}: {len(cards)}")

                            for card in cards:
                                try:
                                    title_elem = card.select_one(".wants-card__header-title a, a[href*='/projects/'], a[href*='/target']")
                                    if not title_elem:
                                        continue

                                    title = title_elem.get_text(strip=True)
                                    raw_href = title_elem.get("href", "").strip()
                                    if not raw_href:
                                        continue

                                    if raw_href.startswith("http://") or raw_href.startswith("https://"):
                                        url = raw_href.replace("kwork.ru", "kwork.com")
                                    else:
                                        if not raw_href.startswith("/"):
                                            raw_href = "/" + raw_href
                                        url = f"https://kwork.com{raw_href}"

                                    desc_elem = card.select_one(".wants-card__description-text, .wants-card__text, div[class*='description']")
                                    description = desc_elem.get_text(strip=True) if desc_elem else title

                                    price_elem = card.select_one(".wants-card__header-price, .price, span[class*='price']")
                                    price = price_elem.get_text(strip=True) if price_elem else "Не указан"

                                    client_elem = card.select_one(".wants-card__user-name, .user-name, a[href*='/user/']")
                                    client = client_elem.get_text(strip=True) if client_elem else "Заказчик Kwork"

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
                                    logger.warning(f"Ошибка разбора карточки Kwork HTML: {card_err}")
                            if orders:
                                break
                except Exception as e:
                    logger.error(f"Ошибка при получении Kwork HTML ({proj_endpoint}): {e}")

        return orders
