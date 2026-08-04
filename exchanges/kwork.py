import logging
import aiohttp
from exchanges.base import Exchange, Order
import config

logger = logging.getLogger(__name__)


class KworkExchange(Exchange):
    """Парсер РЕАЛЬНЫХ покупательских заказов (Wants/Projects) с биржи Kwork."""
    name: str = "Kwork"
    base_url: str = "https://kwork.ru"
    projects_api_url: str = "https://kwork.ru/projects"

    async def fetch_orders(self, session: aiohttp.ClientSession) -> list[Order]:
        orders: list[Order] = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        }

        if config.KWORK_COOKIES:
            headers["Cookie"] = config.KWORK_COOKIES

        # Категории Kwork Биржи заказов: 11 = Разработка и IT
        categories = ["11"]

        for cat_id in categories:
            data = {"c": cat_id, "page": "1"}
            try:
                async with session.post(self.projects_api_url, headers=headers, data=data, timeout=12) as response:
                    if response.status == 200:
                        res = await response.json()
                        wants = res.get("data", {}).get("pagination", {}).get("data", [])
                        logger.info(f"Получено покупательских заказов Kwork (категория {cat_id}): {len(wants)}")

                        for item in wants:
                            try:
                                proj_id = item.get("id")
                                if not proj_id:
                                    continue

                                # Формируем заголовок и описание покупательского проекта
                                title = item.get("title", "").strip()
                                desc = item.get("description", "").strip()
                                
                                if not title or title.lower() == "без названия":
                                    # Если заголовок пустой, берем первые 80 символов описания
                                    title = desc[:80] + ("..." if len(desc) > 80 else "")

                                price_val = item.get("priceLimit", item.get("price", "Договорная"))
                                price_str = f"{price_val} руб." if str(price_val).replace('.', '', 1).isdigit() else str(price_val)

                                client_user = item.get("user", {})
                                client_name = client_user.get("username", item.get("username", "Заказчик Kwork"))
                                
                                deadline = item.get("wantDates", {}).get("dateExpire", "Стандартный")

                                proj_url = f"https://kwork.ru/projects/{proj_id}/view"

                                order = Order(
                                    title=title,
                                    description=desc,
                                    price=price_str,
                                    deadline=deadline,
                                    client=client_name,
                                    source=self.name,
                                    url=proj_url
                                )
                                orders.append(order)
                            except Exception as item_err:
                                logger.warning(f"Ошибка обработки покупательского заказа Kwork: {item_err}")

            except Exception as e:
                logger.error(f"Ошибка запроса покупательских заказов Kwork (категория {cat_id}): {e}")

        return orders
